from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from cats.models import Cat, MedicalRecord, Vaccine
from chat.models import Chat, Message
from matching.models import Match
from users.models import Profile

DEMO_PASSWORD = "Demo1234!"

USERS = [
    {"username": "demo_carlos", "email": "carlos@example.com"},
    {"username": "demo_laura", "email": "laura@example.com"},
    {"username": "demo_andres", "email": "andres@example.com"},
    {"username": "demo_maria", "email": "maria@example.com"},
]

CATS = [
    {"owner": "demo_carlos", "nombre": "Simba", "sexo": "M", "raza": "Persa", "color": "Naranja"},
    {"owner": "demo_laura", "nombre": "Luna", "sexo": "F", "raza": "Siames", "color": "Crema"},
    {"owner": "demo_andres", "nombre": "Milo", "sexo": "M", "raza": "Bengala", "color": "Atigrado"},
    {"owner": "demo_maria", "nombre": "Nala", "sexo": "F", "raza": "Angora", "color": "Blanco"},
]


class Command(BaseCommand):
    help = "Seed demo users, cats (eligible for cruce responsable) and a match/chat/appointment."

    def handle(self, *args, **options):
        with transaction.atomic():
            users = self._create_users()
            cats = self._create_cats(users)
            self._make_eligible(cats)
            self._create_match_flow(cats)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"Login with any of: {', '.join(u['username'] for u in USERS)}")
        self.stdout.write(f"Password: {DEMO_PASSWORD}")

    def _create_users(self):
        users = {}
        for u in USERS:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={"email": u["email"]},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                Profile.objects.create(user=user)
                self.stdout.write(f"Created user {user.username}")
            users[u["username"]] = user
        return users

    def _create_cats(self, users):
        cats = {}
        for c in CATS:
            cat, created = Cat.objects.get_or_create(
                owner=users[c["owner"]],
                nombre=c["nombre"],
                defaults={
                    "raza": c["raza"],
                    "sexo": c["sexo"],
                    "fecha_nacimiento": date.today() - timedelta(days=365 * 2),
                    "peso": 4.2,
                    "color": c["color"],
                    "gustos_preferencias": "Le gusta dormir al sol y jugar con hilos.",
                    "esterilizado": False,
                    "modo_cruce_responsable": True,
                },
            )
            if created:
                self.stdout.write(f"Created cat {cat.nombre} ({cat.owner.username})")
            cats[c["nombre"]] = cat
        return cats

    def _make_eligible(self, cats):
        for cat in cats.values():
            Vaccine.objects.get_or_create(
                gato=cat,
                nombre="Triple Felina",
                defaults={
                    "fecha_aplicacion": date.today() - timedelta(days=30),
                    "fecha_vencimiento": date.today() + timedelta(days=300),
                },
            )
            if not MedicalRecord.objects.filter(gato=cat).exists():
                registro = MedicalRecord(
                    gato=cat,
                    diagnostico_procedimiento="Chequeo general apto para cruce responsable",
                    notas="Sin hallazgos relevantes.",
                )
                registro.documento.save(
                    f"certificado_{cat.nombre.lower()}.txt",
                    ContentFile(f"Certificado medico demo para {cat.nombre}\n".encode()),
                    save=True,
                )

    def _create_match_flow(self, cats):
        simba, luna = cats["Simba"], cats["Luna"]

        match, created = Match.objects.get_or_create(
            gato_emisor=simba,
            gato_receptor=luna,
            defaults={"estado": "ACEPTADO"},
        )
        if created:
            self.stdout.write(f"Created match {simba.nombre} -> {luna.nombre} (ACEPTADO)")
        elif match.estado != "ACEPTADO":
            match.estado = "ACEPTADO"
            match.save()

        chat, _ = Chat.objects.get_or_create(match=match)
        if not Message.objects.filter(chat=chat).exists():
            Message.objects.create(
                chat=chat,
                remitente=simba.owner,
                contenido="Hola! Vi que Luna tambien esta en modo cruce responsable, hablemos.",
            )
            Message.objects.create(
                chat=chat,
                remitente=luna.owner,
                contenido="Hola Carlos! Claro, cuéntame mas sobre Simba.",
            )

        if not Appointment.objects.filter(match=match).exists():
            Appointment.objects.create(
                match=match,
                fecha=timezone.now() + timedelta(days=7),
                ubicacion="Parque Central, Bogota",
                estado="PENDIENTE",
            )

        # Milo (demo_andres) and Nala (demo_maria) are left unmatched on purpose
        # so both accounts have a live candidate to swipe on in matching:swipe.
