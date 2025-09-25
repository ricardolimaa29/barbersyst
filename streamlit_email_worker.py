import streamlit as st
import sqlite3
import smtplib
import threading
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
import os
from io import StringIO

# Configurar logging para capturar no Streamlit


@st.cache_resource
def setup_logging():
    """Configura logging personalizado para Streamlit"""
    log_stream = StringIO()

    # Configurar handler personalizado
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger('email_worker')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger, log_stream


class StreamlitEmailWorker:
    def __init__(self):
        self.logger, self.log_stream = setup_logging()
        self.running = False
        self.ultima_execucao = {}  # Track para evitar execuções muito frequentes

        # Configurações de email (do st.secrets ou session_state)
        self.smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(st.secrets.get("SMTP_PORT", "587"))
        self.email_user = st.secrets.get("EMAIL_USER", "")
        self.email_password = st.secrets.get("EMAIL_PASSWORD", "")
        self.empresa_nome = st.secrets.get("EMPRESA_NOME", "Barbearia")
        self.empresa_telefone = st.secrets.get("EMPRESA_TELEFONE", "")
        self.empresa_endereco = st.secrets.get("EMPRESA_ENDERECO", "")

    def conectar_banco(self) -> sqlite3.Connection:
        """Conecta ao banco de dados"""
        return sqlite3.connect("barbearia.db")

    def buscar_agendamentos_para_envio(self, tipo_envio: int) -> List[Dict]:
        """
        Busca agendamentos que precisam receber email baseado apenas no tempo

        Args:
            tipo_envio: 0=confirmação, 1=lembrete 1 dia, 2=lembrete 30 min
        """
        try:
            conn = self.conectar_banco()
            agora = datetime.now()

            if tipo_envio == 0:  # Confirmação - agendamentos feitos nas últimas 2 horas
                limite_tempo = agora - timedelta(hours=2)
                query = """
                    SELECT 
                        a.id, a.data, a.hora,
                        c.nome as cliente_nome, c.email as cliente_email,
                        s.nome as servico_nome, s.duracao, s.preco
                    FROM agendamentos a
                    JOIN clientes c ON a.cliente_id = c.id
                    JOIN servicos s ON a.servico_id = s.id
                    WHERE a.status = 'agendado' 
                    AND c.email IS NOT NULL 
                    AND c.email != ''
                    AND (a.created_at >= ? OR a.created_at IS NULL)
                    AND a.id NOT IN (
                        SELECT agendamento_id FROM emails_enviados 
                        WHERE tipo_email = 'confirmacao' AND agendamento_id IS NOT NULL
                    )
                    LIMIT 10
                """
                params = (limite_tempo.strftime('%Y-%m-%d %H:%M:%S'),)

            # Lembrete 1 dia antes (entre 20-28 horas antes)
            elif tipo_envio == 1:
                inicio_janela = agora + timedelta(hours=20)
                fim_janela = agora + timedelta(hours=28)

                query = """
                    SELECT 
                        a.id, a.data, a.hora,
                        c.nome as cliente_nome, c.email as cliente_email,
                        s.nome as servico_nome, s.duracao, s.preco
                    FROM agendamentos a
                    JOIN clientes c ON a.cliente_id = c.id
                    JOIN servicos s ON a.servico_id = s.id
                    WHERE a.status = 'agendado' 
                    AND c.email IS NOT NULL 
                    AND c.email != ''
                    AND datetime(a.data || ' ' || a.hora) BETWEEN ? AND ?
                    AND a.id NOT IN (
                        SELECT agendamento_id FROM emails_enviados 
                        WHERE tipo_email = 'lembrete_1dia' AND agendamento_id IS NOT NULL
                    )
                    LIMIT 5
                """
                params = (inicio_janela.strftime('%Y-%m-%d %H:%M:%S'),
                          fim_janela.strftime('%Y-%m-%d %H:%M:%S'))

            # tipo_envio == 2 - Lembrete 30 minutos antes (até 30 minutos antes)
            else:
                limite_tempo = agora + timedelta(minutes=30)

                query = """
                    SELECT 
                        a.id, a.data, a.hora,
                        c.nome as cliente_nome, c.email as cliente_email,
                        s.nome as servico_nome, s.duracao, s.preco
                    FROM agendamentos a
                    JOIN clientes c ON a.cliente_id = c.id
                    JOIN servicos s ON a.servico_id = s.id
                    WHERE a.status = 'agendado' 
                    AND c.email IS NOT NULL 
                    AND c.email != ''
                    AND datetime(a.data || ' ' || a.hora) <= ?
                    AND datetime(a.data || ' ' || a.hora) > ?
                    AND a.id NOT IN (
                        SELECT agendamento_id FROM emails_enviados 
                        WHERE tipo_email = 'lembrete_30min' AND agendamento_id IS NOT NULL
                    )
                    LIMIT 5
                """
                params = (limite_tempo.strftime('%Y-%m-%d %H:%M:%S'),
                          agora.strftime('%Y-%m-%d %H:%M:%S'))

            cursor = conn.execute(query, params)
            agendamentos = []

            for row in cursor.fetchall():
                agendamento_data = {
                    'id': row[0],
                    'data': row[1],
                    'hora': row[2],
                    'cliente_nome': row[3],
                    'cliente_email': row[4],
                    'servico_nome': row[5],
                    'duracao': row[6],
                    'preco': row[7]
                }

                # Para confirmação, incluir created_at se disponível
                if tipo_envio == 0 and len(row) > 8:
                    agendamento_data['created_at'] = row[3]

                agendamentos.append(agendamento_data)

            conn.close()
            return agendamentos

        except Exception as e:
            self.logger.error(f"Erro ao buscar agendamentos: {e}")
            return []

    def buscar_clientes_inativos(self) -> List[Dict]:
        """
        Busca clientes que não fazem agendamento há mais de 20 dias
        e que não receberam email de retorno nos últimos 20 dias
        """
        try:
            conn = self.conectar_banco()
            vinte_dias_atras = datetime.now() - timedelta(days=20)

            query = """
                SELECT DISTINCT
                    c.nome as cliente_nome, 
                    c.email as cliente_email,
                    MAX(a.data) as ultimo_agendamento
                FROM clientes c
                JOIN agendamentos a ON c.id = a.cliente_id
                WHERE c.email IS NOT NULL 
                AND c.email != ''
                AND a.data <= ?
                AND c.email NOT IN (
                    SELECT ee.email_cliente FROM emails_enviados ee 
                    WHERE ee.tipo_email = 'retorno_cliente' 
                    AND ee.data_envio >= ?
                )
                GROUP BY c.nome, c.email
                HAVING MAX(a.data) <= ?
                LIMIT 10
            """

            params = (
                vinte_dias_atras.strftime('%Y-%m-%d'),
                vinte_dias_atras.strftime('%Y-%m-%d %H:%M:%S'),
                vinte_dias_atras.strftime('%Y-%m-%d')
            )

            cursor = conn.execute(query, params)
            clientes = []

            for row in cursor.fetchall():
                clientes.append({
                    'cliente_nome': row[0],
                    'cliente_email': row[1],
                    'ultimo_agendamento': row[2]
                })

            conn.close()
            return clientes

        except Exception as e:
            self.logger.error(f"Erro ao buscar clientes inativos: {e}")
            return []

    def buscar_clientes_sem_agendamento(self) -> List[Dict]:
        """
        Busca clientes que nunca fizeram agendamento e não receberam 
        email promocional nos últimos 20 dias
        """
        try:
            conn = self.conectar_banco()
            vinte_dias_atras = datetime.now() - timedelta(days=20)

            query = """
                SELECT 
                    c.nome as cliente_nome,
                    c.email as cliente_email,
                    c.created_at as data_cadastro
                FROM clientes c
                WHERE c.email IS NOT NULL 
                AND c.email != ''
                AND c.id NOT IN (
                    SELECT DISTINCT a.cliente_id 
                    FROM agendamentos a 
                    WHERE a.cliente_id = c.id
                )
                AND c.email NOT IN (
                    SELECT ee.email_cliente FROM emails_enviados ee 
                    WHERE ee.tipo_email = 'promocional_novo' 
                    AND ee.data_envio >= ?
                )
                LIMIT 10
            """

            params = (vinte_dias_atras.strftime('%Y-%m-%d %H:%M:%S'),)

            cursor = conn.execute(query, params)
            clientes = []

            for row in cursor.fetchall():
                clientes.append({
                    'cliente_nome': row[0],
                    'cliente_email': row[1],
                    'data_cadastro': row[2] if row[2] else 'Não informado'
                })

            conn.close()
            return clientes

        except Exception as e:
            self.logger.error(f"Erro ao buscar clientes sem agendamento: {e}")
            return []

    def criar_tabela_emails_enviados(self):
        """Cria tabela para controlar emails enviados se não existir"""
        try:
            conn = self.conectar_banco()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emails_enviados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agendamento_id INTEGER,
                    tipo_email TEXT NOT NULL,
                    email_cliente TEXT NOT NULL,
                    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sucesso BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (agendamento_id) REFERENCES agendamentos (id)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Erro ao criar tabela de emails: {e}")

    def registrar_email_enviado(self, agendamento_id: int, tipo_email: str, email_cliente: str, sucesso: bool = True):
        """Registra que um email foi enviado"""
        try:
            conn = self.conectar_banco()
            conn.execute("""
                INSERT INTO emails_enviados (agendamento_id, tipo_email, email_cliente, sucesso)
                VALUES (?, ?, ?, ?)
            """, (agendamento_id, tipo_email, email_cliente, sucesso))
            conn.commit()
            conn.close()
            self.logger.info(
                f"Email registrado: {tipo_email} para agendamento {agendamento_id}")
        except Exception as e:
            self.logger.error(f"Erro ao registrar email: {e}")

    def registrar_email_retorno(self, email_cliente: str, sucesso: bool = True):
        """Registra email de retorno enviado para cliente inativo"""
        try:
            conn = self.conectar_banco()

            conn.execute("""
                INSERT INTO emails_enviados (agendamento_id, tipo_email, email_cliente, sucesso)
                VALUES (NULL, 'retorno_cliente', ?, ?)
            """, (email_cliente, sucesso))

            conn.commit()
            conn.close()
            self.logger.info(f"Email retorno registrado para {email_cliente}")

        except Exception as e:
            self.logger.error(f"Erro ao registrar email retorno: {e}")

    def registrar_email_promocional(self, email_cliente: str, sucesso: bool = True):
        """Registra email promocional enviado para cliente sem agendamento"""
        try:
            conn = self.conectar_banco()

            conn.execute("""
                INSERT INTO emails_enviados (agendamento_id, tipo_email, email_cliente, sucesso)
                VALUES (NULL, 'promocional_novo', ?, ?)
            """, (email_cliente, sucesso))

            conn.commit()
            conn.close()
            self.logger.info(
                f"Email promocional registrado para {email_cliente}")

        except Exception as e:
            self.logger.error(f"Erro ao registrar email promocional: {e}")

    def gerar_template_email(self, agendamento: Dict, tipo_envio: int) -> tuple:
        """Gera o template do email baseado no tipo"""
        nome = agendamento['cliente_nome']
        data_formatada = datetime.strptime(
            agendamento['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        hora = agendamento['hora']
        servico = agendamento['servico_nome']
        preco = f"R$ {agendamento['preco']:.2f}"

        if tipo_envio == 0:  # Confirmação
            assunto = f"Agendamento Confirmado - {self.empresa_nome}"

            corpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50; text-align: center;">Agendamento Confirmado!</h2>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #27ae60; margin-top: 0;">Olá, {nome}!</h3>
                            <p>Seu agendamento foi confirmado com sucesso.</p>
                            
                            <ul style="background: white; padding: 15px; border-left: 4px solid #3498db;">
                                <li><strong>Serviço:</strong> {servico}</li>
                                <li><strong>Data:</strong> {data_formatada}</li>
                                <li><strong>Horário:</strong> {hora}</li>
                                <li><strong>Valor:</strong> {preco}</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; color: #666;">
                            <p><strong>{self.empresa_nome}</strong></p>
                            {f'<p>{self.empresa_telefone}</p>' if self.empresa_telefone else ''}
                        </div>
                    </div>
                </body>
            </html>
            """

        elif tipo_envio == 1:  # Lembrete 1 dia
            assunto = f"Lembrete: Seu agendamento é amanhã - {self.empresa_nome}"

            corpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #e67e22; text-align: center;">Lembrete do seu Agendamento</h2>
                        
                        <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #856404; margin-top: 0;">Olá, {nome}!</h3>
                            <p>Seu agendamento é <strong>em aproximadamente 24 horas</strong>:</p>
                            
                            <ul style="background: white; padding: 15px;">
                                <li><strong>Serviço:</strong> {servico}</li>
                                <li><strong>Data:</strong> {data_formatada}</li>
                                <li><strong>Horário:</strong> {hora}</li>
                                <li><strong>Valor:</strong> {preco}</li>
                            </ul>
                            
                            <p style="margin-top: 15px;"><strong>Não esqueça!</strong> Te esperamos no horário marcado.</p>
                        </div>
                        
                        <div style="text-align: center; color: #666;">
                            <p><strong>{self.empresa_nome}</strong></p>
                            {f'<p>{self.empresa_telefone}</p>' if self.empresa_telefone else ''}
                        </div>
                    </div>
                </body>
            </html>
            """
        else:  # tipo_envio == 2 - 30 minutos
            assunto = f"Seu agendamento é em breve! - {self.empresa_nome}"

            corpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #dc3545; text-align: center;">⏰ Seu agendamento está chegando!</h2>
                        
                        <div style="background-color: #f8d7da; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="color: #721c24; margin-top: 0;">Olá, {nome}!</h3>
                            <p><strong>Seu agendamento é em breve!</strong> Prepare-se para chegar no horário.</p>
                            
                            <ul style="background: white; padding: 15px;">
                                <li><strong>Serviço:</strong> {servico}</li>
                                <li><strong>Data:</strong> {data_formatada}</li>
                                <li><strong>Horário:</strong> {hora}</li>
                            </ul>
                            
                            <p style="margin-top: 15px; font-size: 16px;"><strong>🚗 É hora de sair de casa!</strong></p>
                        </div>
                        
                        <div style="text-align: center; color: #666;">
                            <p><strong>{self.empresa_nome}</strong></p>
                            <p><strong>Te esperamos em breve!</strong></p>
                        </div>
                    </div>
                </body>
            </html>
            """

        # Versão texto
        corpo_texto = f"""
        {assunto}
        
        Olá, {nome}!
        
        Serviço: {servico}
        Data: {data_formatada}
        Horário: {hora}
        Valor: {preco}
        
        {self.empresa_nome}
        """

        return assunto, corpo_html, corpo_texto

    def gerar_template_email_retorno(self, cliente: Dict) -> tuple:
        """Gera template de email para cliente inativo"""
        nome = cliente['cliente_nome']
        ultimo_agendamento = datetime.strptime(
            cliente['ultimo_agendamento'], '%Y-%m-%d').strftime('%d/%m/%Y')

        assunto = f"Sentimos sua falta! - {self.empresa_nome}"

        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; text-align: center;">Sentimos sua falta!</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #27ae60; margin-top: 0;">Olá, {nome}!</h3>
                        <p>Notamos que seu último agendamento foi em <strong>{ultimo_agendamento}</strong> e sentimos muito a sua falta!</p>
                        
                        <ul style="background: white; padding: 15px; border-left: 4px solid #3498db;">
                            <li><strong>Último agendamento:</strong> {ultimo_agendamento}</li>
                            <li><strong>Status:</strong> Cliente especial</li>
                            <li><strong>Convite:</strong> Que tal agendar um novo horário?</li>
                        </ul>
                        
                        <p>Estamos sempre aqui para cuidar de você com o mesmo carinho de sempre.</p>
                    </div>
                    
                    <div style="text-align: center; color: #666;">
                        <p><strong>{self.empresa_nome}</strong></p>
                        {f'<p>{self.empresa_telefone}</p>' if self.empresa_telefone else ''}
                    </div>
                </div>
            </body>
        </html>
        """

        corpo_texto = f"""
        Sentimos sua falta! - {self.empresa_nome}
        
        Olá, {nome}!
        
        Último agendamento: {ultimo_agendamento}
        Status: Cliente especial
        Convite: Que tal agendar um novo horário?
        
        Estamos sempre aqui para cuidar de você com o mesmo carinho de sempre.
        
        {self.empresa_nome}
        """

        return assunto, corpo_html, corpo_texto

    def gerar_template_email_promocional(self, cliente: Dict) -> tuple:
        """Gera template de email promocional para cliente sem agendamento"""
        nome = cliente['cliente_nome']

        assunto = f"Conheça nossos serviços! - {self.empresa_nome}"

        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; text-align: center;">Conheça nossos serviços!</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #27ae60; margin-top: 0;">Olá, {nome}!</h3>
                        <p>Que tal conhecer nossos serviços e agendar seu primeiro horário conosco?</p>
                        
                        <ul style="background: white; padding: 15px; border-left: 4px solid #3498db;">
                            <li><strong>Serviços:</strong> Cortes modernos e clássicos</li>
                            <li><strong>Qualidade:</strong> Profissionais experientes</li>
                            <li><strong>Convite:</strong> Faça seu primeiro agendamento!</li>
                        </ul>
                        
                        <p>Estamos prontos para cuidar de você com todo carinho e profissionalismo.</p>
                    </div>
                    
                    <div style="text-align: center; color: #666;">
                        <p><strong>{self.empresa_nome}</strong></p>
                        {f'<p>{self.empresa_telefone}</p>' if self.empresa_telefone else ''}
                    </div>
                </div>
            </body>
        </html>
        """

        corpo_texto = f"""
        Conheça nossos serviços! - {self.empresa_nome}
        
        Olá, {nome}!
        
        Serviços: Cortes modernos e clássicos
        Qualidade: Profissionais experientes
        Convite: Faça seu primeiro agendamento!
        
        Estamos prontos para cuidar de você com todo carinho e profissionalismo.
        
        {self.empresa_nome}
        """

        return assunto, corpo_html, corpo_texto

    def enviar_email(self, destinatario: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
        """Envia o email"""
        try:
            if not self.email_user or not self.email_password:
                self.logger.warning("Credenciais de email não configuradas")
                return False

            msg = MIMEMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = self.email_user
            msg['To'] = destinatario

            part1 = MIMEText(corpo_texto, 'plain', 'utf-8')
            part2 = MIMEText(corpo_html, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            self.logger.info(f"Email enviado: {destinatario}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar email para {destinatario}: {e}")
            return False

    def processar_envios(self, tipo_envio: int):
        """Processa os envios de email para um tipo específico"""
        # Garantir que a tabela existe
        self.criar_tabela_emails_enviados()

        agendamentos = self.buscar_agendamentos_para_envio(tipo_envio)

        if not agendamentos:
            return 0

        tipos_email = {0: 'confirmacao',
                       1: 'lembrete_1dia', 2: 'lembrete_30min'}
        tipo_nome = tipos_email[tipo_envio]

        enviados = 0
        for agendamento in agendamentos:
            try:
                self.logger.info(
                    f"Processando {tipo_nome} para agendamento {agendamento['id']}")

                assunto, corpo_html, corpo_texto = self.gerar_template_email(
                    agendamento, tipo_envio)

                sucesso = self.enviar_email(
                    agendamento['cliente_email'],
                    assunto,
                    corpo_html,
                    corpo_texto
                )

                # Registrar tentativa de envio
                self.registrar_email_enviado(
                    agendamento['id'],
                    tipo_nome,
                    agendamento['cliente_email'],
                    sucesso
                )

                if sucesso:
                    enviados += 1
                    self.logger.info(
                        f"{tipo_nome.capitalize()} enviado para agendamento {agendamento['id']}")
                else:
                    self.logger.error(
                        f"Falha ao enviar {tipo_nome} para agendamento {agendamento['id']}")

                # Pequena pausa entre emails
                time.sleep(2)

            except Exception as e:
                self.logger.error(
                    f"Erro ao processar agendamento {agendamento['id']}: {e}")
                self.registrar_email_enviado(
                    agendamento['id'],
                    tipo_nome,
                    agendamento['cliente_email'],
                    False
                )

        if enviados > 0:
            self.logger.info(f"Total {tipo_nome}: {enviados} emails enviados")

        return enviados

    def processar_emails_retorno(self):
        """Processa envios de email para clientes inativos"""
        clientes = self.buscar_clientes_inativos()

        if not clientes:
            return 0

        enviados = 0
        for cliente in clientes:
            try:
                self.logger.info(
                    f"Processando email retorno para {cliente['cliente_email']}")

                assunto, corpo_html, corpo_texto = self.gerar_template_email_retorno(
                    cliente)

                sucesso = self.enviar_email(
                    cliente['cliente_email'],
                    assunto,
                    corpo_html,
                    corpo_texto
                )

                self.registrar_email_retorno(
                    cliente['cliente_email'],
                    sucesso
                )

                if sucesso:
                    enviados += 1
                    self.logger.info(
                        f"Email retorno enviado para {cliente['cliente_email']}")

                time.sleep(2)  # Pausa entre emails

            except Exception as e:
                self.logger.error(
                    f"Erro ao processar cliente {cliente['cliente_email']}: {e}")
                self.registrar_email_retorno(cliente['cliente_email'], False)

        if enviados > 0:
            self.logger.info(f"Total emails retorno: {enviados} enviados")

        return enviados

    def processar_emails_promocionais(self):
        """Processa envios de email promocional para clientes sem agendamento"""
        clientes = self.buscar_clientes_sem_agendamento()

        if not clientes:
            return 0

        enviados = 0
        for cliente in clientes:
            try:
                self.logger.info(
                    f"Processando email promocional para {cliente['cliente_email']}")

                assunto, corpo_html, corpo_texto = self.gerar_template_email_promocional(
                    cliente)

                sucesso = self.enviar_email(
                    cliente['cliente_email'],
                    assunto,
                    corpo_html,
                    corpo_texto
                )

                self.registrar_email_promocional(
                    cliente['cliente_email'],
                    sucesso
                )

                if sucesso:
                    enviados += 1
                    self.logger.info(
                        f"Email promocional enviado para {cliente['cliente_email']}")

                time.sleep(2)  # Pausa entre emails

            except Exception as e:
                self.logger.error(
                    f"Erro ao processar cliente {cliente['cliente_email']}: {e}")
                self.registrar_email_promocional(
                    cliente['cliente_email'], False)

        if enviados > 0:
            self.logger.info(f"Total emails promocionais: {enviados} enviados")

        return enviados

    def executar_verificacao_unica(self):
        """Executa uma verificação manual de todos os tipos"""
        resultados = {
            'confirmacoes': 0,
            'lembretes_1dia': 0,
            'lembretes_30min': 0,
            'emails_retorno': 0,
            'emails_promocionais': 0,
            'erros': []
        }

        try:
            self.logger.info("Iniciando verificação manual completa")

            # Confirmações
            resultados['confirmacoes'] = self.processar_envios(0)

            # Lembretes 1 dia
            resultados['lembretes_1dia'] = self.processar_envios(1)

            # Lembretes 30 min
            resultados['lembretes_30min'] = self.processar_envios(2)

            # Emails de retorno e promocionais
            resultados['emails_retorno'] = self.processar_emails_retorno()
            resultados['emails_promocionais'] = self.processar_emails_promocionais()

            total_enviados = (resultados['confirmacoes'] +
                              resultados['lembretes_1dia'] +
                              resultados['lembretes_30min'] +
                              resultados['emails_retorno'] +
                              resultados['emails_promocionais'])
            self.logger.info(
                f"Verificação concluída: {total_enviados} emails enviados")

        except Exception as e:
            resultados['erros'].append(str(e))
            self.logger.error(f"Erro na verificação: {e}")

        return resultados

    def worker_background(self):
        """Worker que roda em background"""
        self.logger.info("Worker iniciado em background")
        self.running = True

        while self.running:
            try:
                agora = datetime.now()
                deve_executar = False

                if agora.minute % 2 == 0:  # A cada 2 minutos ao invés de 5
                    deve_executar = True

                # Evitar execuções muito próximas (menos de 90 segundos)
                if deve_executar:
                    ultima_exec = self.ultima_execucao.get(
                        'automatica', datetime.min)
                    if (agora - ultima_exec).total_seconds() < 90:
                        deve_executar = False

                if deve_executar:
                    self.logger.info(
                        f"Executando verificação automática às {agora.strftime('%H:%M')}")

                    # Executar todos os tipos de envio
                    conf = self.processar_envios(0)  # Confirmações
                    lem1 = self.processar_envios(1)  # Lembretes 1 dia
                    lem30 = self.processar_envios(2)  # Lembretes 30 min
                    ret = self.processar_emails_retorno()  # Emails de retorno
                    prom = self.processar_emails_promocionais()  # Emails promocionais

                    total = conf + lem1 + lem30 + ret + prom
                    if total > 0:
                        self.logger.info(
                            f"Verificação automática: {total} emails enviados (C:{conf}, L1:{lem1}, L30:{lem30}, R:{ret}, P:{prom})")

                    self.ultima_execucao['automatica'] = agora

                # Sleep menor para mais responsividade
                time.sleep(30)  # Verificar a cada 30 segundos ao invés de 60

            except Exception as e:
                self.logger.error(f"Erro no worker: {e}")
                time.sleep(60)

    def iniciar_worker_background(self):
        """Inicia o worker em thread separada"""
        if not self.running:
            thread = threading.Thread(
                target=self.worker_background, daemon=True)
            thread.start()

    def parar_worker(self):
        """Para o worker"""
        self.running = False
        self.logger.info("Worker parado")

    def obter_estatisticas_emails(self):
        """Obtém estatísticas dos emails enviados"""
        try:
            conn = self.conectar_banco()

            # Verificar se a tabela existe
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='emails_enviados'
            """)

            if not cursor.fetchone():
                conn.close()
                return {"hoje": 0, "total": 0, "por_tipo": {}}

            hoje = datetime.now().date()

            # Emails de hoje
            cursor = conn.execute("""
                SELECT COUNT(*) FROM emails_enviados 
                WHERE date(data_envio) = ? AND sucesso = 1
            """, (hoje,))
            emails_hoje = cursor.fetchone()[0]

            # Total de emails
            cursor = conn.execute("""
                SELECT COUNT(*) FROM emails_enviados WHERE sucesso = 1
            """)
            total_emails = cursor.fetchone()[0]

            # Por tipo
            cursor = conn.execute("""
                SELECT tipo_email, COUNT(*) FROM emails_enviados 
                WHERE sucesso = 1 GROUP BY tipo_email
            """)
            por_tipo = dict(cursor.fetchall())

            conn.close()

            return {
                "hoje": emails_hoje,
                "total": total_emails,
                "por_tipo": por_tipo
            }

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {"hoje": 0, "total": 0, "por_tipo": {}}

    def verificar_status_worker(self):
        """Verifica se o worker ainda está ativo"""
        # Verificar se há threads ativas
        threads_ativas = [t for t in threading.enumerate(
        ) if t.name.startswith('Thread') and t.daemon]

        status = {
            'running': self.running,
            'threads_daemon': len(threads_ativas),
            'ultima_execucao': self.ultima_execucao.get('automatica', 'Nunca'),
            'tempo_desde_ultima': None
        }

        if isinstance(status['ultima_execucao'], datetime):
            delta = datetime.now() - status['ultima_execucao']
            status['tempo_desde_ultima'] = f"{delta.total_seconds():.0f}s atrás"

        return status

    def executar_verificacao_forcada(self):
        """Executa verificação forçada, ignorando timers e verificações"""
        self.logger.info("Executando verificação FORÇADA")

        resultados = {
            'confirmacoes': 0,
            'lembretes_1dia': 0,
            'lembretes_30min': 0,
            'emails_retorno': 0,
            'emails_promocionais': 0,
            'erros': []
        }

        try:
            # Garantir que a tabela existe
            self.criar_tabela_emails_enviados()

            # Confirmações
            agendamentos_conf = self.buscar_agendamentos_para_envio(0)
            self.logger.info(
                f"Encontrados {len(agendamentos_conf)} agendamentos para confirmação")

            for ag in agendamentos_conf:
                try:
                    assunto, corpo_html, corpo_texto = self.gerar_template_email(
                        ag, 0)
                    sucesso = self.enviar_email(
                        ag['cliente_email'], assunto, corpo_html, corpo_texto)
                    self.registrar_email_enviado(
                        ag['id'], 'confirmacao', ag['cliente_email'], sucesso)
                    if sucesso:
                        resultados['confirmacoes'] += 1
                except Exception as e:
                    resultados['erros'].append(
                        f"Erro confirmação {ag['id']}: {str(e)}")

            # Lembretes 1 dia
            agendamentos_1d = self.buscar_agendamentos_para_envio(1)
            self.logger.info(
                f"Encontrados {len(agendamentos_1d)} agendamentos para lembrete 1 dia")

            for ag in agendamentos_1d:
                try:
                    assunto, corpo_html, corpo_texto = self.gerar_template_email(
                        ag, 1)
                    sucesso = self.enviar_email(
                        ag['cliente_email'], assunto, corpo_html, corpo_texto)
                    self.registrar_email_enviado(
                        ag['id'], 'lembrete_1dia', ag['cliente_email'], sucesso)
                    if sucesso:
                        resultados['lembretes_1dia'] += 1
                except Exception as e:
                    resultados['erros'].append(
                        f"Erro lembrete 1d {ag['id']}: {str(e)}")

            # Lembretes 30 min
            agendamentos_30m = self.buscar_agendamentos_para_envio(2)
            self.logger.info(
                f"Encontrados {len(agendamentos_30m)} agendamentos para lembrete 30min")

            for ag in agendamentos_30m:
                try:
                    assunto, corpo_html, corpo_texto = self.gerar_template_email(
                        ag, 2)
                    sucesso = self.enviar_email(
                        ag['cliente_email'], assunto, corpo_html, corpo_texto)
                    self.registrar_email_enviado(
                        ag['id'], 'lembrete_30min', ag['cliente_email'], sucesso)
                    if sucesso:
                        resultados['lembretes_30min'] += 1
                except Exception as e:
                    resultados['erros'].append(
                        f"Erro lembrete 30m {ag['id']}: {str(e)}")

            # Emails de retorno
            clientes_inativos = self.buscar_clientes_inativos()
            self.logger.info(
                f"Encontrados {len(clientes_inativos)} clientes inativos")

            for cliente in clientes_inativos:
                try:
                    assunto, corpo_html, corpo_texto = self.gerar_template_email_retorno(
                        cliente)
                    sucesso = self.enviar_email(
                        cliente['cliente_email'], assunto, corpo_html, corpo_texto)
                    self.registrar_email_retorno(
                        cliente['cliente_email'], sucesso)
                    if sucesso:
                        resultados['emails_retorno'] += 1
                except Exception as e:
                    resultados['erros'].append(
                        f"Erro email retorno cliente {cliente['cliente_email']}: {str(e)}")

            # Emails promocionais
            clientes_sem_agendamento = self.buscar_clientes_sem_agendamento()
            self.logger.info(
                f"Encontrados {len(clientes_sem_agendamento)} clientes sem agendamento")

            for cliente in clientes_sem_agendamento:
                try:
                    assunto, corpo_html, corpo_texto = self.gerar_template_email_promocional(
                        cliente)
                    sucesso = self.enviar_email(
                        cliente['cliente_email'], assunto, corpo_html, corpo_texto)
                    self.registrar_email_promocional(
                        cliente['cliente_email'], sucesso)
                    if sucesso:
                        resultados['emails_promocionais'] += 1
                except Exception as e:
                    resultados['erros'].append(
                        f"Erro email promocional cliente {cliente['cliente_email']}: {str(e)}")

            total = (resultados['confirmacoes'] +
                     resultados['lembretes_1dia'] +
                     resultados['lembretes_30min'] +
                     resultados['emails_retorno'] +
                     resultados['emails_promocionais'])
            self.logger.info(
                f"Verificação forçada concluída: {total} emails enviados")

        except Exception as e:
            resultados['erros'].append(f"Erro geral: {str(e)}")
            self.logger.error(f"Erro na verificação forçada: {e}")

        return resultados


# Função para inicializar o worker no Streamlit
@st.cache_resource
def inicializar_email_worker():
    """Inicializa o worker de email (executa apenas uma vez)"""
    worker = StreamlitEmailWorker()
    worker.iniciar_worker_background()
    return worker


# Interface do usuário no Streamlit
def exibir_interface_email_worker():
    """Exibe a interface de controle do email worker"""
    st.subheader("📧 Sistema de Envio de Emails (Baseado em Tempo)")

    # Inicializar worker
    if 'email_worker' not in st.session_state:
        st.session_state.email_worker = inicializar_email_worker()

    # Atualizar atividade
    st.session_state.last_activity = datetime.now()

    worker = st.session_state.email_worker

    # Status detalhado do worker
    status = worker.verificar_status_worker()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_text = "🟢 Ativo" if status['running'] else "🔴 Parado"
        st.metric("Status Worker", status_text)

    with col2:
        st.metric("Threads Daemon", status['threads_daemon'])

    with col3:
        ultima = status['tempo_desde_ultima'] or "Nunca"
        st.metric("Última Execução", ultima)

    with col4:
        # Estatísticas
        stats = worker.obter_estatisticas_emails()
        st.metric("Emails Hoje", stats["hoje"])

    # Botão para verificação manual
    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("🔄 Verificar Agora", help="Executa verificação manual"):
            with st.spinner("Verificando agendamentos..."):
                resultados = worker.executar_verificacao_unica()

                st.success("Verificação concluída!")

                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                with col_a:
                    st.metric("Confirmações", resultados['confirmacoes'])
                with col_b:
                    st.metric("Lembretes 1 dia", resultados['lembretes_1dia'])
                with col_c:
                    st.metric("Lembretes 30min", resultados['lembretes_30min'])
                with col_d:
                    st.metric("Emails Retorno", resultados['emails_retorno'])
                with col_e:
                    st.metric("Emails Promocionais",
                              resultados['emails_promocionais'])

                if resultados['erros']:
                    st.error(f"Erros: {', '.join(resultados['erros'])}")

    with col_btn2:
        if st.button("⚡ Verificação FORÇADA", help="Executa verificação forçada ignorando timers"):
            with st.spinner("Executando verificação forçada..."):
                resultados = worker.executar_verificacao_forcada()
                st.success("Verificação forçada concluída!")

                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                with col_a:
                    st.metric("Confirmações", resultados['confirmacoes'])
                with col_b:
                    st.metric("Lembretes 1 dia", resultados['lembretes_1dia'])
                with col_c:
                    st.metric("Lembretes 30min", resultados['lembretes_30min'])
                with col_d:
                    st.metric("Emails Retorno", resultados['emails_retorno'])
                with col_e:
                    st.metric("Emails Promocionais",
                              resultados['emails_promocionais'])

                if resultados['erros']:
                    with st.expander("❌ Erros encontrados"):
                        for erro in resultados['erros']:
                            st.error(erro)

    with col_btn3:
        if st.button("🔄 Reiniciar Worker"):
            worker.parar_worker()
            time.sleep(1)
            worker.iniciar_worker_background()
            st.success("Worker reiniciado!")
            st.rerun()

    # Estatísticas por tipo
    if stats["por_tipo"]:
        st.write("**Emails por tipo:**")
        for tipo, quantidade in stats["por_tipo"].items():
            st.write(f"• {tipo.replace('_', ' ').title()}: {quantidade}")

    # Diagnóstico do Sistema
    with st.expander("🔍 Diagnóstico do Sistema"):
        st.write("**Status detalhado do Worker:**")
        for key, value in status.items():
            st.write(f"• {key}: {value}")

        # Testar credenciais
        if worker.email_user and worker.email_password:
            st.success("✅ Credenciais de email configuradas")
        else:
            st.error("❌ Credenciais de email não configuradas")

        # Verificar agendamentos disponíveis
        agendamentos_info = {
            'Confirmações pendentes': len(worker.buscar_agendamentos_para_envio(0)),
            'Lembretes 1 dia pendentes': len(worker.buscar_agendamentos_para_envio(1)),
            'Lembretes 30min pendentes': len(worker.buscar_agendamentos_para_envio(2)),
            'Emails retorno pendentes': len(worker.buscar_clientes_inativos()),
            'Emails promocionais pendentes': len(worker.buscar_clientes_sem_agendamento())
        }

        st.write("**Agendamentos disponíveis para envio:**")
        for tipo, quantidade in agendamentos_info.items():
            emoji = "📧" if quantidade > 0 else "✅"
            st.write(f"{emoji} {tipo}: {quantidade}")

    # Configurações
    with st.expander("⚙️ Configurações de Email"):
        st.info(
            "Configure as credenciais em **st.secrets** para ativar o envio de emails")

        # Mostrar configurações atuais (sem senhas)
        config_atual = {
            "SMTP Server": worker.smtp_server,
            "SMTP Port": worker.smtp_port,
            "Email User": worker.email_user if worker.email_user else "❌ Não configurado",
            "Email Password": "✅ Configurada" if worker.email_password else "❌ Não configurada",
            "Empresa Nome": worker.empresa_nome,
            "Empresa Telefone": worker.empresa_telefone or "Não configurado",
        }

        for key, value in config_atual.items():
            st.text(f"{key}: {value}")

        st.code("""
# Adicione ao arquivo .streamlit/secrets.toml:
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
EMAIL_USER = "seu_email@gmail.com"
EMAIL_PASSWORD = "sua_senha_de_app"
EMPRESA_NOME = "BarberSyst"
EMPRESA_TELEFONE = "(11) 99999-9999"
EMPRESA_ENDERECO = "Rua Exemplo, 123"
        """)

    # Como funciona
    with st.expander("ℹ️ Como Funciona o Sistema - VERSÃO COMPLETA"):
        st.markdown("""
        **Sistema baseado em tempo real:**
        
        • **Confirmações**: Enviadas para agendamentos criados nas últimas 2 horas
        • **Lembretes 1 dia**: Enviados quando faltam entre 20-28 horas para o agendamento
        • **Lembretes 30 min**: Enviados quando faltam até 30 minutos para o agendamento
        • **Emails de Retorno**: Enviados para clientes inativos (mais de 20 dias sem agendamento)
        • **Emails Promocionais**: Enviados para clientes que nunca fizeram agendamento (a cada 20 dias)
        
        **Verificações automáticas:**
        • A cada 2 minutos (ao invés de 5 minutos)
        • Verificação a cada 30 segundos (ao invés de 60 segundos)
        • Controle de execuções muito próximas (mínimo 90 segundos entre execuções)
        
        **Controles de spam:**
        • Clientes inativos: só recebem novo email após 20 dias do último email de retorno
        • Clientes sem agendamento: só recebem novo email após 20 dias do último email promocional
        • Agendamentos: só recebem um email de cada tipo (confirmação, lembrete 1 dia, lembrete 30 min)
        
        **Funcionalidades:**
        • ✅ Worker background automático
        • ✅ Verificação manual e forçada
        • ✅ Logs detalhados de todas as operações
        • ✅ Estatísticas completas por tipo de email
        • ✅ Diagnóstico completo do sistema
        """)

    # Logs do worker
    with st.expander("📋 Logs do Sistema"):
        if st.button("🔄 Atualizar Logs"):
            st.rerun()

        # Mostrar últimos logs
        logs_content = worker.log_stream.getvalue()
        if logs_content:
            # Mostrar apenas últimas 50 linhas
            logs_lines = logs_content.strip().split('\n')[-50:]
            st.text('\n'.join(logs_lines))
        else:
            st.info("Nenhum log disponível ainda")


# Exemplo de como usar na sua aplicação principal
if __name__ == "__main__":
    st.title("Sistema de Barbearia - Email Worker v3.0 COMPLETO")

    # Inicializar sistema de emails automaticamente
    exibir_interface_email_worker()

    st.markdown("---")
    st.success(
        "✨ O sistema de emails está completo e funcionando com todas as funcionalidades!")
    st.info("""
    **Funcionalidades implementadas:**
    - ✅ Confirmações de agendamento (2 horas após criar)
    - ✅ Lembretes 1 dia antes (20-28 horas antes)
    - ✅ Lembretes 30 minutos antes
    - ✅ Emails de retorno para clientes inativos (20+ dias sem agendar)
    - ✅ Emails promocionais para clientes sem agendamento (a cada 20 dias)
    - ✅ Worker automático rodando em background
    - ✅ Interface completa com diagnósticos e logs
    """)
