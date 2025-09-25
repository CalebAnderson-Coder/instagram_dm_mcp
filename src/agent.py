import os
import time
import random
import sqlite3
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired
import logging
import google.generativeai as genai
# =================================================================================================

# Load environment variables from .env file
load_dotenv()

# Set up logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Persona and Knowledge Base for "Alejandro Rojas" ---
SYSTEM_PROMPT = """
Eres **Alejandro Rojas**, experto en soluciones energéticas de EcoFlow y especialista en ventas consultivas para el mercado venezolano. Tu misión es identificar las necesidades energéticas específicas de cada cliente y conectar emocionalmente con los problemas de energía eléctrica que enfrentan los venezolanos diariamente.

**Personalidad:** Empático, técnicamente competente, orientado a soluciones, y profundamente conocedor de la realidad energética venezolana.
"""

VENEZUELA_CONTEXT = """
**REALIDAD ENERGÉTICA VENEZOLANA:**
- Cortes eléctricos frecuentes: Promedio de 4-6 horas diarias en muchas zonas.
- Crisis eléctrica crónica: Más de 24,000 interrupciones registradas en 2023.
- Afectación nacional: Apagones que impactan hasta el 80% del territorio.
- Sectores críticos afectados: Hogares, empresas, hospitales, telecomunicaciones.
- Impacto económico: Pérdidas de productividad, daños a equipos, negocios paralizados.

**OPORTUNIDADES DE MERCADO:**
- Creciente demanda de soluciones energéticas independientes.
- Mercado de energía portátil en expansión.
- Necesidad urgente de respaldo energético confiable.
"""

ECOFLOW_KNOWLEDGE_BASE = """
**LÍNEA DELTA (Para uso doméstico y comercial):**

**DELTA 2**
- Capacidad: 1024 Wh
- Precio: $640

**DELTA Pro**
- Capacidad: 3600 Wh
- Precio: $1,360

**DELTA Max**
- Capacidad: 2016 Wh
- Precio: $1,999

**DELTA 2 Max**
- Capacidad: 2048 Wh
- Precio: $2,334

**LÍNEA RIVER (Portabilidad máxima):**

**River 2**
- Capacidad: 256 Wh
- Precio: $271

**River 2 Max**
- Capacidad: 512 Wh
- Precio: $364

**River 2 Pro**
- Capacidad: 768 Wh
- Precio: $636 (Nota: Precio actualizado de la imagen)

**River 3**
- Capacidad: 245 Wh
- Precio: $338
"""

SALES_METHODOLOGY = """
**PROCESO DE DESCUBRIMIENTO:**

1. **Identificación de Dolor:**
   - "¿Con qué frecuencia experimentas cortes de luz en tu zona?"
   - "¿Qué equipos son más críticos para ti durante un apagón?"
   - "¿Has tenido pérdidas económicas o de productividad por los cortes eléctricos?"

2. **Cuantificación del Problema:**
   - "¿Cuántas horas al día necesitas respaldo energético?"
   - "¿Qué potencia consumen tus equipos esenciales? (nevera, router, laptop, etc.)"
   - "¿Cuál es el costo actual de no tener energía?"

3. **Exploración de Necesidades Específicas:**
   - ¿Es para tu hogar o para un negocio?
   - ¿Necesitas mover la estación de energía con frecuencia?
   - ¿Cuál es tu presupuesto aproximado?
"""

INITIAL_MESSAGE_TEMPLATES = [
    "Hola {full_name}! 👋 Vi que sigues a @{target_account} y te interesan las soluciones de energía. Como experto de EcoFlow en Venezuela, entiendo perfectamente los retos que vivimos con los cortes de luz. Tenemos las mejores ofertas en estaciones de energía EcoFlow, con hasta 30% de descuento en modelos nuevos y garantía extendida. ¿Te gustaría que te ayude a encontrar la solución perfecta para ti? Podemos conversar por aquí o, si prefieres, te paso mi contacto de WhatsApp para una asesoría más directa. ¡Saludos! Alejandro Rojas",
    "¡Qué tal, {full_name}! 😊 Noté que sigues a @{target_account}, así que imagino que te interesa la energía de respaldo. Soy Alejandro Rojas, especialista de EcoFlow aquí en Venezuela. Conozco de primera mano lo frustrante que son los apagones. Por eso te comento que tenemos promociones increíbles en estaciones EcoFlow, ideales para no quedarte sin luz. Si quieres, te asesoro para que encuentres la mejor opción. ¿Hablamos por aquí o prefieres por WhatsApp? ¡Un abrazo!",
    "Saludos, {full_name}. Mi nombre es Alejandro Rojas, de EcoFlow Venezuela. Vi tu interés en @{target_account} y quería contactarte. Sé lo complicado que es el tema eléctrico en nuestro país. Te comento que tenemos descuentos de hasta el 30% en equipos nuevos. Si buscas una solución energética confiable, estoy a la orden para ayudarte a elegir la ideal. ¿Te parece si conversamos por DM o te contacto por WhatsApp? Gracias por tu tiempo.",
    "Hola {full_name}, ¿cómo estás? Soy Alejandro Rojas, experto en energía de EcoFlow. Vi que sigues a @{target_account} y me animé a escribirte. En Venezuela, tener un respaldo de energía es clave. Justo ahora, tenemos unas ofertas excelentes en estaciones EcoFlow. Si te interesa, puedo darte todos los detalles sin compromiso para que veas cuál se adapta mejor a tus necesidades. ¿Te viene bien por aquí o te paso mi WhatsApp? ¡Que tengas un buen día!"
]

# =================================================================================================
# MAIN AGENT CLASS
# =================================================================================================

class InstagramAppointmentSetter:
    def __init__(self, username, password, verification_code=None, api_key=None, db_path=None):
        self.client = Client()
        self.my_user_id = None
        self.username = username
        self.password = password
        self.verification_code = verification_code
        # Use custom database path if provided, otherwise use default
        self.db_path = db_path or "leads.db"
        self._setup_database()

        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Google AI SDK configured successfully.")
        else:
            self.model = None
            logger.warning("API key not provided. Conversational features will be disabled.")

    def _setup_database(self):
        """Initializes the SQLite database and creates the leads table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT,
                status TEXT DEFAULT 'contacted', -- contacted, replied, qualified, transferred, ignored
                last_contacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversation_history TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database '{self.db_path}' setup complete.")

    def login(self):
        """Logs into Instagram, handling sessions and 2FA."""
        session_file = f"{self.username}_agent_session.json"
        try:
            if os.path.exists(session_file):
                logger.info(f"Loading session from {session_file}")
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
            else:
                logger.info("No session file found, performing fresh login.")
                self.client.login(self.username, self.password)
        except TwoFactorRequired:
            if not self.verification_code:
                logger.error("2FA required, but no verification code provided.")
                raise
            self.client.login(self.username, self.password, verification_code=self.verification_code)
        
        self.client.dump_settings(session_file)
        self.my_user_id = self.client.user_id
        logger.info(f"Login successful. Session saved to {session_file}. Logged in as user ID: {self.my_user_id}")

    def get_followers(self, target_username, amount=500):
        """Gets a list of followers from a target account."""
        logger.info(f"Fetching followers for {target_username}...")
        try:
            user_id = self.client.user_id_from_username(target_username)
            followers = self.client.user_followers(user_id, amount=amount)
            logger.info(f"Successfully fetched {len(followers)} followers.")
            return list(followers.values())
        except Exception as e:
            logger.error(f"Could not fetch followers for {target_username}: {e}")
            return []

    def send_initial_message(self, user, target_account):
        """Sends the initial outreach message to a user and logs it to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user has already been contacted
        cursor.execute("SELECT user_id FROM leads WHERE user_id = ?", (user.pk,))
        if cursor.fetchone():
            logger.info(f"User {user.username} has already been contacted. Skipping.")
            conn.close()
            return False

        try:
            template = random.choice(INITIAL_MESSAGE_TEMPLATES)
            message = template.format(full_name=user.full_name or user.username, target_account=target_account)
            self.client.direct_send(message, user_ids=[user.pk])
            
            # Log to database
            cursor.execute(
                "INSERT INTO leads (user_id, username, full_name, status) VALUES (?, ?, ?, ?)",
                (user.pk, user.username, user.full_name, 'contacted')
            )
            conn.commit()
            logger.info(f"Successfully sent initial message to {user.username}.")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {user.username}: {e}")
            return False
        finally:
            conn.close()

    def monitor_and_process_replies(self):
        """Monitors DM threads for replies from contacted leads and updates the database."""
        logger.info("Checking for new replies...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get leads that we are waiting for a reply from
            cursor.execute("SELECT user_id, username FROM leads WHERE status = 'contacted'")
            contacted_leads = cursor.fetchall()
            contacted_user_ids = {lead[0] for lead in contacted_leads}

            if not contacted_user_ids:
                logger.info("No pending leads to check for replies.")
                return

            # Fetch recent DM threads
            threads = self.client.direct_threads(amount=50) # Increased amount
            
            for thread in threads:
                # Check if any participant in the thread is a contacted lead
                thread_user_ids = {str(user.pk) for user in thread.users}
                lead_in_thread = contacted_user_ids.intersection(thread_user_ids)

                if lead_in_thread:
                    lead_id = lead_in_thread.pop()
                    
                    # Fetch the full thread to get messages
                    full_thread = self.client.direct_thread(thread.id)
                    if not full_thread or not full_thread.messages:
                        continue

                    last_message = full_thread.messages[0] # Messages are sorted newest to oldest
                    
                    logger.debug(f"Thread with {lead_id}. Last message from user_id: {last_message.user_id}. My user_id: {self.my_user_id}")
                    # A simple check: if the last message is not from us, it's a reply
                    if str(last_message.user_id) != str(self.my_user_id):
                        logger.info(f"Detected a reply from user_id: {lead_id} (username: {thread.users[0].username})")
                        
                        # Update lead status and save conversation
                        conversation_history = f"LEAD: {last_message.text}\n"
                        cursor.execute(
                            "UPDATE leads SET status = 'replied', conversation_history = ?, last_contacted_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                            (conversation_history, lead_id)
                        )
                        conn.commit()
                        logger.info(f"Updated lead {lead_id} to 'replied' status.")
                        
                        # Generate and send an intelligent reply
                        self.generate_and_send_reply(lead_id, conversation_history)

        except Exception as e:
            logger.error(f"An error occurred while monitoring replies: {e}")
        finally:
            conn.close()

    def generate_and_send_reply(self, user_id, conversation_history):
        """Generates a reply using the LLM and sends it to the user."""
        if not self.model:
            logger.warning("Cannot generate reply: LLM model not initialized.")
            return

        logger.info(f"Generating reply for user_id: {user_id}")
        
        # Construct the prompt for the LLM
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"**Contexto de Venezuela:**\n{VENEZUELA_CONTEXT}\n\n"
            f"**Base de Conocimiento de Productos:**\n{ECOFLOW_KNOWLEDGE_BASE}\n\n"
            f"**Metodología de Ventas:**\n{SALES_METHODOLOGY}\n\n"
            f"**Historial de la Conversación:**\n{conversation_history}\n\n"
            "**Tu Tarea:** Responde al último mensaje del lead de manera empática y consultiva. "
            "Usa tu conocimiento para guiar la conversación, identificar sus necesidades y acercarlo a una solución. "
            "Si te piden precios, usa la base de conocimiento. Si hacen preguntas técnicas, respóndelas. "
            "Tu objetivo es calificar al lead. No termines la conversación, siempre haz una pregunta abierta para continuar."
            "\n\n**Tu Respuesta (como Alejandro Rojas):**"
        )

        try:
            response = self.model.generate_content(full_prompt)
            reply_text = response.text

            # Send the reply via Instagram DM
            self.client.direct_send(reply_text, user_ids=[user_id])
            logger.info(f"Successfully sent reply to {user_id}: {reply_text}")

            # Update conversation history in the database
            updated_history = f"{conversation_history}ALEJANDRO: {reply_text}\n"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE leads SET conversation_history = ? WHERE user_id = ?",
                (updated_history, user_id)
            )
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to generate or send reply for {user_id}: {e}")

    def run(self, target_account="ecoflowpower_ve", daily_limit=30, check_interval_minutes=30):
        """Main loop for the agent. Sends outreach messages and checks for replies."""
        logger.info("Agent started.")
        self.login()
        
        while True:
            # --- Dynamic Outreach and Monitoring Cycle ---
            logger.info("Starting new dynamic cycle...")

            # 1. Always check for replies first. This is the priority.
            self.monitor_and_process_replies()

            # 2. Check how many messages have been sent today.
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads WHERE DATE(last_contacted_at) = DATE('now', 'localtime')")
            messages_sent_today = cursor.fetchone()[0]
            conn.close()
            logger.info(f"Messages sent today: {messages_sent_today}. Daily limit: {daily_limit}.")

            # 3. If the daily limit has not been reached, proceed with sending new messages.
            if messages_sent_today < daily_limit:
                logger.info("Daily limit not reached. Proceeding with outreach.")
                followers = self.get_followers(target_account, amount=daily_limit * 2)
                
                if not followers:
                    logger.warning("No new followers found for outreach.")
                else:
                    for follower in followers:
                        # Re-check the count before each send
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM leads WHERE DATE(last_contacted_at) = DATE('now', 'localtime')")
                        messages_sent_today = cursor.fetchone()[0]
                        conn.close()

                        if messages_sent_today >= daily_limit:
                            logger.info("Daily message limit reached during outreach cycle.")
                            break
                        
                        if self.send_initial_message(follower, target_account):
                            delay = random.uniform(90, 120) # Keep safe delay
                            logger.info(f"Waiting for {delay:.2f} seconds...")
                            time.sleep(delay)
            else:
                logger.info("Daily message limit reached. Switching to reply-monitoring only mode.")

            # 4. Wait for the next cycle.
            final_wait_minutes = 5 if messages_sent_today >= daily_limit else check_interval_minutes
            logger.info(f"Cycle finished. Waiting for {final_wait_minutes} minutes...")
            time.sleep(final_wait_minutes * 60)


if __name__ == "__main__":
    ig_username = os.getenv("INSTAGRAM_USERNAME")
    ig_password = os.getenv("INSTAGRAM_PASSWORD")
    ig_2fa_code = os.getenv("INSTAGRAM_VERIFICATION_CODE")
    api_key = os.getenv("API_KEY")

    if not ig_username or not ig_password:
        logger.error("Instagram credentials not found in .env file.")
    elif not api_key:
        logger.warning("API_KEY not found in .env file. Conversational features will be disabled.")
    
    agent = InstagramAppointmentSetter(
        username=ig_username,
        password=ig_password,
        verification_code=ig_2fa_code,
        api_key=api_key
    )
    agent.run()
