#!/usr/bin/env python

import argparse
from collections.abc import Sequence
import liquid
import os.path
from pathlib import Path
import shutil
import sys

def _generate_versions(jd_root: Path) -> dict[str, list[str]]: # module -> list[version]
  """
  Generate a mapping of adventure module to module version.
  """
  result = {}

  for module in jd_root.iterdir():
    dirname = module.name
    if dirname.startswith(".") or dirname.startswith("_") or not module.is_dir():
      continue

    versions = [x.name for x in module.iterdir() if x.is_dir and not x.name.startswith(".")]
    result[dirname] = versions

  return result

def _create_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="Generate static content for JD site")
  parser.add_argument('dest', type=Path, help="Directory to generate to")
  parser.add_argument('--jd-root', type=Path, help="Directory to search for module Javadoc in", default='.')

  script_dir = Path(__file__).parent

  parser.add_argument("--template-root", type=Path, help="Directory to read templates from", default = script_dir / 'tmpl')
  parser.add_argument("--static-root", type=Path, help="Static root, for files copied directly", default = script_dir / 'static')
  return parser

def _do_generate(dest: Path, jd_root: Path, template_root: Path, static_root: Path):
  print(f"Generating from jd={jd_root}, tmpl={template_root}, static={static_root} -> {dest}")

  # Setup, generate metadata
  module_versions = _generate_versions(jd_root)
  shutil.rmtree(dest)
  dest.mkdir(exist_ok=True)

  # Generate templates
  tmpl_env = liquid.Environment(
    loader=liquid.FileSystemLoader(template_root),
    globals={
      "module_versions": module_versions
    },
    undefined=liquid.StrictUndefined
  )

  for tmpl in template_root.glob('**/*'):
    tmpl_out = dest / tmpl
    print(f"Writing {tmpl} to {tmpl_out}")
    template = tmpl_env.get_template(str(tmpl))
    with tmpl_out.open(mode = 'wt') as fp:
      fp.write(template.render())

  # Copy static content
  for static in static_root.glob('**/*'):
    static_out = dest / static
    print(f"Writing {static} to {static_out}")
    shutil.copy2(static, static_out)

  # link JD directories into the output dir
  for module in module_versions.keys():
    module_out = dest / module
    print(f"Linking {module} to {module_out}")
    module_out.symlink_to(os.path.relpath(jd_root.absolute() / module, start=module_out), target_is_directory=True)

  print(f"Generated successfully to {dest}")

def main(args: Sequence[str]):
  parser = _create_parser()
  parsed = parser.parse_args(args)
  _do_generate(parsed.dest, parsed.jd_root, parsed.template_root, parsed.static_root)

if __name__ == "__main__":
  main(sys.argv[1:])
