#!/usr/bin/env python

import argparse
from collections.abc import Sequence
import jinja2
import os.path
from pathlib import Path
import shutil
import sys
from typing import NamedTuple

class ModuleVersions(NamedTuple):
  name: str
  versions: list[str]


def _generate_versions(jd_root: Path) -> list[ModuleVersions]: # module -> list[version]
  """
  Generate a mapping of adventure module to module version.
  """
  result = []

  for module in jd_root.iterdir():
    dirname = module.name
    if dirname.startswith(".") or dirname.startswith("_") or not module.is_dir():
      continue

    versions = [x.name for x in module.iterdir() if x.is_dir and not x.name.startswith(".")]
    result.append(ModuleVersions(dirname, versions))

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
  if dest.exists():
    shutil.rmtree(dest)
  dest.mkdir(exist_ok=True)

  # Generate templates
  tmpl_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_root),
    undefined=jinja2.StrictUndefined,
    autoescape=True,
    keep_trailing_newline=True
  )
  tmpl_env.globals["module_versions"] = module_versions

  for tmpl in template_root.glob('**/*'):
    tmpl_out = dest / tmpl.relative_to(template_root)
    print(f"Writing {tmpl} to {tmpl_out}")
    template = tmpl_env.get_template(str(tmpl.relative_to(template_root)))
    with tmpl_out.open(mode = 'wt') as fp:
      fp.write(template.render())

  # Copy static content
  for static in static_root.glob('**/*'):
    static_out = dest / static.relative_to(static_root)
    print(f"Writing {static} to {static_out}")
    shutil.copy2(static, static_out)

  # link JD directories into the output dir
  for module in module_versions:
    module_out = dest / module.name
    print(f"Copying {module.name} to {module_out}")
    shutil.copytree(jd_root / module.name, module_out, symlinks=True)

  print(f"Generated successfully to {dest}")

def main(args: Sequence[str]):
  parser = _create_parser()
  parsed = parser.parse_args(args)
  _do_generate(parsed.dest, parsed.jd_root, parsed.template_root, parsed.static_root)

if __name__ == "__main__":
  main(sys.argv[1:])
