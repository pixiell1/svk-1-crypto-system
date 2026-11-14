from core.fingerprint import SystemFingerprint

fp = SystemFingerprint()
print("=== Данные о системе ===")
for k, v in fp.get_details().items():
    print(f"{k}: {v}")

print("\n=== Итоговый отпечаток (SHA-256) ===")
print(fp.get_fingerprint())