# agent/ — Agente Python Windows

Servicio Python instalado en el PC del cliente.
Conecta Firebird (Saiopen) con AWS SQS.

Flujo:
Firebird → Agent → SQS saisuite-to-cloud.fifo → Django
Django → SQS saisuite-to-saiopen.fifo → Agent → Firebird
