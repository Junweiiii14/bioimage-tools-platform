"""Configure official CP modules for development; no segmentation implementation."""

import argparse
import hashlib
import re
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    expected = "7b35c66b775b5a25d0e39f917e0c52982ff2605017ded9c0cd0dc39a206b0138"
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != expected:
        raise ValueError("Official example archive hash mismatch")
    with zipfile.ZipFile(args.archive) as archive:
        original = archive.read("ExampleHuman/ExampleHuman.cppipe").decode("utf-8")
    blocks = re.split(r"\n\s*\n", original.strip())
    header, modules = blocks[0], blocks[1:]
    if len(modules) != 14:
        raise ValueError("Unexpected official module structure")
    selected = modules[:5]
    names = selected[2]
    names = names.replace("Assignments count:3", "Assignments count:1")
    start = names.index('    Select the rule criteria:and (file does contain "d1.tif")')
    names = names[:start].rstrip()
    names = names.replace('and (file does contain "d0.tif")', "and (extension does istif)")
    selected[2] = names
    # Development-only preset: accommodate observed 13-130 px equivalent diameters.
    # Keep the official automatic declumping and minimum cross-entropy threshold.
    selected[4] = selected[4].replace("(Min,Max):8,80", "(Min,Max):8,160")
    selected[4] = selected[4].replace(
        "Discard objects outside the diameter range?:Yes",
        "Discard objects outside the diameter range?:No",
    )
    selected[4] = selected[4].replace(
        "Discard objects touching the border of the image?:Yes",
        "Discard objects touching the border of the image?:No",
    )
    selected.append(
        "ConvertObjectsToImage:[module_num:6|"
        "svn_version:'Unknown'|variable_revision_number:1|"
        "show_window:False|notes:[]|batch_state:array([], dtype=uint8)|"
        "enabled:True|wants_pause:False]\n"
        "    Select the input objects:Nuclei\n"
        "    Name the output image:NucleiLabels\n"
        "    Select the color format:uint16\n"
        "    Select the colormap:Default"
    )
    save = modules[12].replace("module_num:13", "module_num:7")
    save = save.replace(
        "Select the image to save:OrigOverlay", "Select the image to save:NucleiLabels"
    )
    save = save.replace(
        "Text to append to the image name:_Overlay", "Text to append to the image name:_labels"
    )
    # Official SaveImages npy branch writes label IDs without display conversion.
    save = save.replace("Saved file format:png", "Saved file format:npy")
    save = save.replace(
        "Overwrite existing files without warning?:Yes",
        "Overwrite existing files without warning?:No",
    )
    selected.append(save)
    export = modules[13].replace("module_num:14", "module_num:8")
    export = export.replace(
        "Overwrite existing files without warning?:Yes",
        "Overwrite existing files without warning?:No",
    )
    selected.append(export)
    text = "\n\n".join([header.replace("ModuleCount:14", "ModuleCount:8"), *selected]) + "\n"
    text = text.replace("show_window:True", "show_window:False")
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
