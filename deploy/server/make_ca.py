"""Sinh CA offline và leaf; tất cả đầu ra phải nằm ngoài repo/worktree."""

import argparse
import datetime as dt
import ipaddress
import os
import re
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def output_path(value):
    path = Path(value).resolve()
    if any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise ValueError("Không ghi cert/khoá vào repo hoặc worktree")
    if path.exists():
        raise FileExistsError("Đầu ra đã tồn tại; không ghi đè")
    return path


def san_name(value):
    try:
        return x509.IPAddress(ipaddress.ip_address(value))
    except ValueError:
        if len(value) > 253 or not all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in value.split(".")
        ):
            raise ValueError("SAN phải là IP hoặc DNS hợp lệ") from None
        return x509.DNSName(value)


def generate(root_dir, leaf_dir, sans, leaf_days):
    if type(leaf_days) is not int or not 1 <= leaf_days <= 3650:
        raise ValueError("Hạn leaf phải là số ngày trong 1..3650")
    if not sans:
        raise ValueError("Phải cung cấp ít nhất một SAN")
    names = [san_name(value) for value in sans]
    # Kiểm mọi đường dẫn trước khi tạo thư mục hoặc file đầu tiên.
    paths = [output_path(Path(root_dir) / name) for name in ("root.key", "ca.crt")]
    paths += [output_path(Path(leaf_dir) / name) for name in ("leaf.key", "leaf.crt")]
    if len(set(paths)) != len(paths):
        raise ValueError("Các đầu ra không được trùng nhau")
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    start = now - dt.timedelta(minutes=5)
    root_key = ec.generate_private_key(ec.SECP256R1())
    leaf_key = ec.generate_private_key(ec.SECP256R1())
    root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "FlexMix offline CA")])
    root = (x509.CertificateBuilder().subject_name(root_name).issuer_name(root_name)
            .public_key(root_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(start).not_valid_after(now + dt.timedelta(days=3651))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, key_cert_sign=True, crl_sign=True,
                content_commitment=False, key_encipherment=False, data_encipherment=False,
                key_agreement=False, encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()), critical=False)
            .sign(root_key, hashes.SHA256()))
    leaf = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, sans[0])]))
            .issuer_name(root_name).public_key(leaf_key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(start)
            .not_valid_after(start + dt.timedelta(days=leaf_days))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName(names), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(root_key.public_key()), critical=False)
            .sign(root_key, hashes.SHA256()))
    private = lambda key: key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    data = (private(root_key), root.public_bytes(serialization.Encoding.PEM),
            private(leaf_key), leaf.public_bytes(serialization.Encoding.PEM))
    created = []
    try:
        for path, content in zip(paths, data):
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            created.append(path)
            with os.fdopen(fd, "wb") as stream:
                if os.name != "nt":
                    os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
    except BaseException:
        for path in reversed(created):
            path.unlink()
        raise
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root-dir", required=True, help="Nơi giữ root offline ngoài repo")
    parser.add_argument("--leaf-dir", required=True, help="Nơi giữ leaf ngoài repo")
    parser.add_argument("--san", action="append", required=True, help="IP/DNS; lặp lại cho nhiều SAN")
    parser.add_argument("--leaf-days", type=int, required=True, help="Hạn leaf; Q4 chưa có mặc định")
    args = parser.parse_args()
    try:
        generate(args.root_dir, args.leaf_dir, args.san, args.leaf_days)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print("Đã sinh root và leaf ngoài repo. Giữ root.key offline; không chép lên server.")


if __name__ == "__main__":
    main()
