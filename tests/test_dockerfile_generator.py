from pathlib import Path

import pytest

from modules.dockerfile_generator import DockerfileGenerator

LANGUAGES = ["python", "java", "node", "groovy", "robot", "go", "dotnet"]


@pytest.fixture
def generator():
    return DockerfileGenerator({})


@pytest.mark.parametrize("language", LANGUAGES)
def test_generates_multi_stage_dockerfile(generator, tmp_path, language):
    path = generator.generate(language, str(tmp_path))

    assert path == str(tmp_path / "Dockerfile")
    content = Path(path).read_text()
    assert content.count("FROM") >= 2, "template should be multi-stage"
    assert "USER" in content, "template should drop root privileges"


def test_unsupported_language_returns_none(generator, tmp_path):
    assert generator.generate("rust", str(tmp_path)) is None


def test_custom_base_image_is_used(generator, tmp_path):
    generator.generate("python", str(tmp_path), base_image="python:3.12-slim")

    content = (tmp_path / "Dockerfile").read_text()
    assert "FROM python:3.12-slim" in content


def test_custom_args_override_defaults(generator, tmp_path):
    generator.generate("python", str(tmp_path), custom_args={"port": "9000"})

    content = (tmp_path / "Dockerfile").read_text()
    assert "9000" in content
