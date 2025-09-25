# Instagram DM Agent MVP

Un prototipo funcional de un agente automatizado para mensajes directos en Instagram, diseñado para appointment setters y vendedores.

## 🚀 Características

- **Automatización Completa**: Envía mensajes iniciales y responde automáticamente a las respuestas usando IA.
- **Interfaz Visual**: Dashboard web intuitivo con control en tiempo real del agente.
- **Dashboard de KPIs**: Métricas clave para medir el rendimiento de tus campañas.
- **IA Conversacional**: Respuestas personalizadas usando Google Gemini AI.
- **Límites de Seguridad**: Respeta los límites diarios de Instagram para evitar suspensiones.

## 📋 Requisitos

- Python 3.8+
- Cuenta de Instagram
- API Key de Google AI (Gemini)

## 🛠️ Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/CalebAnderson-Coder/instagram_dm_mcp.git
   cd instagram_dm_mcp
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las variables de entorno:**
   Crea un archivo `.env` con:
   ```
   INSTAGRAM_USERNAME=tu_usuario_instagram
   INSTAGRAM_PASSWORD=tu_contraseña
   API_KEY=tu_api_key_de_google_ai
   ```

## 🎯 Uso

### Opción 1: Interfaz Web (Recomendado)

1. **Inicia el servidor:**
   ```bash
   python main.py
   ```

2. **Abre tu navegador:**
   Ve a `http://localhost:8000`

3. **Configura el agente:**
   - Completa el formulario con tus credenciales
   - Especifica la cuenta objetivo (sin @)
   - Presiona "Iniciar Agente"

4. **Monitorea el rendimiento:**
   - Cambia a la pestaña "Dashboard de KPIs"
   - Ve las métricas en tiempo real

### Opción 2: Script Directo

```bash
python src/agent.py
```

## 📊 KPIs Disponibles

- **Mensajes Enviados Hoy**: Total de mensajes iniciales enviados
- **Respuestas Recibidas**: Número de usuarios que respondieron
- **Tasa de Respuesta**: Porcentaje de respuestas sobre mensajes enviados
- **Leads Calificados**: Conversaciones que recibieron respuesta de la IA
- **Tasa de Calificación**: Porcentaje de leads calificados sobre respuestas

## 🤖 Cómo Funciona la IA

El agente usa "Alejandro Rojas" como personalidad:

- **Especialista en EcoFlow**: Conoce productos de energía portátil
- **Orientado a Ventas**: Usa metodología consultiva para calificar leads
- **Contexto Venezolano**: Entiende los problemas de energía en Venezuela
- **Respuestas Empáticas**: Conecta emocionalmente con los usuarios

## ⚠️ Consideraciones de Seguridad

- **Límites Diarios**: Máximo 30 mensajes por día por cuenta
- **Tiempos de Espera**: Espera aleatoria entre mensajes (90-120 segundos)
- **Sesiones**: Guarda sesiones para evitar logins frecuentes
- **2FA**: Soporte para autenticación de dos factores

## 🏗️ Arquitectura

```
├── main.py              # API FastAPI (Backend)
├── index.html           # Interfaz web (Frontend)
├── script.js            # Lógica JavaScript
├── src/
│   ├── agent.py         # Lógica principal del agente
│   ├── logger.py        # Sistema de logging
│   └── mcp_server.py   # Servidor MCP (opcional)
└── leads.db            # Base de datos SQLite
```

## 🔧 Personalización

### Cambiar la Personalidad de la IA

Edita las constantes en `src/agent.py`:
- `SYSTEM_PROMPT`: Personalidad del agente
- `VENEZUELA_CONTEXT`: Contexto específico
- `INITIAL_MESSAGE_TEMPLATES`: Plantillas de mensajes

### Modificar KPIs

Edita el endpoint `/api/kpis` en `main.py` para añadir nuevas métricas.

## 📈 Próximas Mejoras

- [ ] Dashboard con gráficos históricos
- [ ] Exportación de datos a CSV/Excel
- [ ] Múltiples campañas simultáneas
- [ ] Integración con CRM
- [ ] Análisis de sentimientos en respuestas

## 📞 Soporte

Para soporte técnico o preguntas:
- Revisa los logs en la consola
- Verifica que todas las dependencias estén instaladas
- Asegúrate de que las credenciales sean correctas

## ⚖️ Descargo de Responsabilidad

Este software es para fines educativos y comerciales legítimos. El uso indebido puede violar los términos de servicio de Instagram. Úsalo responsablemente y respeta las políticas de la plataforma.

---

**Versión:** 1.0.0 MVP
**Última actualización:** Septiembre 2025
