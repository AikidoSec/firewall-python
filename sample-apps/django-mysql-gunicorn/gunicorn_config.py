from dotenv import load_dotenv
import os
load_dotenv()
firewall_disabled = os.getenv("FIREWALL_DISABLED")
if firewall_disabled is not None:
    if firewall_disabled.lower() != "1":
        import aikido_firewall.middleware.django_gunicorn as aik
        @aik.when_ready
        def when_ready(server): pass
        @aik.post_fork
        def post_fork(server, worker): pass
