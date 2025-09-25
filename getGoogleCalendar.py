from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'barbersyst@gmail.com'


def get_google_service():
    """Retorna o serviço autenticado do Google Calendar"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Força a porta 8080 para corresponder à configuração
            creds = flow.run_local_server(port=8080)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def criar_evento_calendar(agendamento):
    """
    Cria evento no Google Calendar
    agendamento: dict com keys: data, hora, duracao, cliente_nome, servico_nome, preco, status
    Retorna: google_event_id ou None
    """
    try:
        service = get_google_service()

        start_dt = datetime.strptime(
            f"{agendamento['data']} {agendamento['hora']}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=agendamento['duracao'])

        event = {
            'summary': f"{agendamento['servico_nome']} - {agendamento['cliente_nome']}",
            'description': f"Preço: R$ {agendamento['preco']:.2f}\nStatus: {agendamento['status']}",
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Sao_Paulo'},
        }

        created_event = service.events().insert(
            calendarId=CALENDAR_ID, body=event).execute()
        return created_event['id']
    except:
        return None


def atualizar_evento_calendar(google_event_id, agendamento):
    """
    Atualiza evento no Google Calendar
    Retorna: True se sucesso, False se erro
    """
    try:
        service = get_google_service()

        start_dt = datetime.strptime(
            f"{agendamento['data']} {agendamento['hora']}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=agendamento['duracao'])

        event = service.events().get(calendarId=CALENDAR_ID,
                                     eventId=google_event_id).execute()

        event['summary'] = f"{agendamento['servico_nome']} - {agendamento['cliente_nome']}"
        event['description'] = f"Preço: R$ {agendamento['preco']:.2f}\nStatus: {agendamento['status']}"
        event['start']['dateTime'] = start_dt.isoformat()
        event['end']['dateTime'] = end_dt.isoformat()

        service.events().update(calendarId=CALENDAR_ID,
                                eventId=google_event_id, body=event).execute()
        return True
    except:
        return False


def deletar_evento_calendar(google_event_id):
    """
    Deleta evento do Google Calendar
    Retorna: True se sucesso, False se erro
    """
    try:
        service = get_google_service()
        service.events().delete(calendarId=CALENDAR_ID, eventId=google_event_id).execute()
        return True
    except:
        return False
