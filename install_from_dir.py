import asyncio
import json
import plistlib
import sys
from pathlib import Path

from pymobiledevice3.remote.userspace_tunnel import establish_userspace_rsd
from pymobiledevice3.remote.xpc_message import XpcUInt64Type
from pymobiledevice3.services.cryptexd import CryptexAssetType, CryptexdService

UDID = "INSERT UDID"


def read(path: Path) -> bytes:
    return path.read_bytes()


async def main() -> None:
    root = Path(sys.argv[1]).resolve()
    persistence = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    nonce_persistence = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    auth = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    rsd = await establish_userspace_rsd(serial=UDID)
    service = CryptexdService(rsd)

    before = await service.copy_installed()
    print("BEFORE")
    print(json.dumps([entry.__dict__ for entry in before], indent=2, sort_keys=True))

    props = plistlib.loads(read(root / "cx1p"))
    cryptex1_properties = {
        "Cryptex1,UseProductClass": props["Cryptex1,UseProductClass"],
        "MountedCryptex": props["MountedCryptex"],
        "Cryptex1,SubType": XpcUInt64Type(props["Cryptex1,SubType"]),
        "Cryptex1,NonceDomain": XpcUInt64Type(props["Cryptex1,NonceDomain"]),
        "Cryptex1,Version": props["Cryptex1,Version"],
        "Cryptex1,PreauthVersion": props["Cryptex1,PreauthVersion"],
    }
    identifier = plistlib.loads(read(root / "ginf"))["CFBundleIdentifier"]
    try:
        await service.install(
            image=read(root / "gdmg"),
            trustcache=read(root / "gtcd"),
            im4m=read(root / "im4m"),
            info=read(root / "ginf"),
            volumehash=read(root / "gtgv"),
            cryptex1_properties=cryptex1_properties,
            image_type_index=CryptexAssetType.GDMG,
            persistence=persistence,
            nonce_persistence=nonce_persistence,
            auth=auth,
        )
    except Exception as e:
        print(f"INSTALL_FAILED: {e!r}")
        raise
    print("INSTALL_OK")
    installed = await service.copy_installed()
    print(json.dumps([entry.__dict__ for entry in installed], indent=2, sort_keys=True))
    match = next((entry for entry in installed if entry.identifier == identifier), None)
    print(f"TARGET_PRESENT={match is not None}")
    if match is not None:
        print(f"TARGET_VERSION={match.version}")


if __name__ == "__main__":
    asyncio.run(main())
