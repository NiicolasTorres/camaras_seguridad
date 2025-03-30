from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import os, base64
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings

def generate_or_load_vapid_keys():
    # Verifica si las claves existen
    if os.path.exists(settings.VAPID_PRIVATE_KEY) and os.path.exists(settings.VAPID_PUBLIC_KEY):
        with open(settings.VAPID_PRIVATE_KEY, "rb") as key_file:
            private_key_obj = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )
        with open(settings.VAPID_PUBLIC_KEY, "rb") as key_file:
            public_key_pem = key_file.read()
            public_key_obj = serialization.load_pem_public_key(public_key_pem)
    else:
        # Genera nuevas claves si no existen
        private_key_obj = ec.generate_private_key(ec.SECP256R1())
        public_key_obj = private_key_obj.public_key()

        # Guarda las claves en archivos
        with open(settings.VAPID_PRIVATE_KEY, "wb") as key_file:
            key_file.write(private_key_obj.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(settings.VAPID_PUBLIC_KEY, "wb") as key_file:
            key_file.write(public_key_obj.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    print("Claves VAPID generadas o cargadas.")

    # Convertir la clave pública al formato "uncompressed" (65 bytes) usando X9.62
    public_key_bytes = public_key_obj.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip("=")

    # Convertir la clave privada a DER (como ya lo hacías)
    private_key_der = private_key_obj.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    vapid_private_key_b64 = base64.urlsafe_b64encode(private_key_der).decode('utf-8').rstrip("=")

    return vapid_private_key_b64, public_key_b64
