"""Opt-in disposable installation identity; existing distribution profiles stay fixed."""

import re


def acceptance_identity(identifier: str) -> dict[str, object]:
    if re.fullmatch(r"[a-z][a-z0-9-]{0,31}", identifier) is None:
        raise ValueError("acceptance-id must match [a-z][a-z0-9-]{0,31}")
    return {
        "acceptance_id": identifier,
        "distribution_id": f"BioImageTools.WB.Acceptance.{identifier}",
        "release_channel": f"wb-acceptance-{identifier}",
        "settings_namespace": f"Acceptance-{identifier}",
        "executable": "BioImageWB-Acceptance.exe",
        "default_install_directory": f"Programs/BioImage WB 验收 {identifier}",
        "shortcut_name": f"BioImage WB 验收 {identifier}",
        "user_data_removal": False,
    }
