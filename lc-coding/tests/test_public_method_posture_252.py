from pathlib import Path


root = Path(__file__).resolve().parents[2]


def require(relative, *markers):
    text = (root / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker.casefold() in text.casefold(), f"{relative}: {marker}"


require(
    "README.md",
    "personal ability, knowledge structure, and recurring project practice",
    "study and adapt LCCoding",
    "discussion and contributions",
    "canonical mainline",
)
require(
    "README.zh-CN.md",
    "个人能力、知识结构和经常处理的项目实践",
    "借鉴并按自己的能力、知识范围和项目条件微调",
    "讨论和贡献",
    "规范主线",
)

print("PASS: public method posture preserves adaptable use and canonical ownership")
