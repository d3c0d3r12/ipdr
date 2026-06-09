# backend/utils/letter_template.py
"""Schema + default for ISP letter templates (block-based)."""
from __future__ import annotations
from typing import Annotated, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator

PLACEHOLDERS: List[str] = [
    "fir_number", "fir_date", "letter_date", "police_station", "sections",
    "complainant", "isp_name", "officer_name", "officer_designation",
    "officer_location", "officer_contact", "subject", "email_reference",
]


def substitute(text: str, values: dict) -> str:
    """Replace every {token} with its value (empty string if missing)."""
    out = text
    for token in PLACEHOLDERS:
        value = values.get(token)
        out = out.replace("{" + token + "}", "" if value is None else str(value))
    return out


class PageSettings(BaseModel):
    margins_inches: Dict[str, float] = Field(
        default_factory=lambda: {"top": 0.5, "bottom": 0.5, "left": 0.75, "right": 0.75}
    )
    default_font: str = "Calibri"
    default_size: int = 10


class TextBlock(BaseModel):
    id: str
    type: Literal["text"] = "text"
    content: str = ""
    align: Literal["left", "center", "right"] = "left"
    bold: bool = False
    italic: bool = False
    font: Optional[str] = None
    size: Optional[int] = Field(default=None, gt=0)


class ListBlock(BaseModel):
    id: str
    type: Literal["list"] = "list"
    style: Literal["numbered", "bullet"] = "numbered"
    items: List[str] = Field(default_factory=list)
    font: Optional[str] = None
    size: Optional[int] = Field(default=None, gt=0)


class IpTableBlock(BaseModel):
    id: str
    type: Literal["ip_table"] = "ip_table"


class SpacerBlock(BaseModel):
    id: str
    type: Literal["spacer"] = "spacer"
    lines: int = Field(default=1, ge=1)


Block = Annotated[
    Union[TextBlock, ListBlock, IpTableBlock, SpacerBlock],
    Field(discriminator="type"),
]


class LetterTemplate(BaseModel):
    name: str
    owner_id: Optional[str] = None
    scope: Literal["system", "user", "shared"] = "user"
    page: PageSettings = Field(default_factory=PageSettings)
    blocks: List[Block]

    @model_validator(mode="after")
    def _at_most_one_ip_table(self):
        n = sum(1 for b in self.blocks if b.type == "ip_table")
        if n > 1:
            raise ValueError("A template may contain at most one ip_table block")
        return self


def _t(id, content, **kw):
    return {"id": id, "type": "text", "content": content, **kw}


DEFAULT_TEMPLATE = {
    "name": "IFSO Dwarka Default",
    "owner_id": None,
    "scope": "system",
    "page": {
        "margins_inches": {"top": 0.5, "bottom": 0.5, "left": 0.75, "right": 0.75},
        "default_font": "Calibri",
        "default_size": 10,
    },
    "blocks": [
        _t("legal", "Seeking data under the statutory provisions contained in Section 94 of the "
                    "Bharatiya Nagarik Suraksha Sanhita, 2023 or Section 5(2) of the Indian Telegraph "
                    "Act, 1885 read with Rule 419A of the Indian Telegraph (Amendment) Rules, 2007.",
           align="center", italic=True, size=10),
        _t("office_name", "OFFICE OF THE CYBER CRIME UNIT, IFSO, SPECIAL CELL, DELHI POLICE,",
           align="center", bold=True, size=11),
        _t("office_addr", "SEC - 16C, DWARKA, NEW DELHI - 110078", align="center", size=10),
        _t("office_contact", "Contact No. 011-20892632, E-Mail ID : acp-cybercell1@delhipolice.gov.in",
           align="center", size=9),
        _t("notice", "Notice u/s 94 BNSS, 2023", align="center", bold=True, size=11),
        {"id": "sp1", "type": "spacer", "lines": 1},
        _t("to", "To,\n     The Nodal Officer\n     {isp_name}"),
        _t("subject", "Subject:- {subject} FIR No. {fir_number}, PS {police_station} ({email_reference})",
           bold=True),
        _t("salutation", "Sir,"),
        _t("body", "                It is submitted that case FIR No.{fir_number}, U/s {sections}, "
                   "Dated {fir_date}, PS {police_station}, Delhi has been registered on the complaint "
                   "of {complainant} at IFSO/CCU/Spl. Cell, New Delhi. During investigation the "
                   "following IP details/numbers have emerged as suspect."),
        _t("req_intro", "You are hereby requested to provide the following information/documents:-"),
        {"id": "reqs", "type": "list", "style": "numbered", "items": [
            "Details of the user (Name, Address, Contact No. etc.) to whom below IP's were allotted "
            "at the mentioned Date & time against each.",
            "Kindly provide the ownership of the users, to whom IP was allotted.",
            "Kindly preserve the record till further directions.",
            "Kindly provide any other useful details.",
        ]},
        _t("urgent", "The above-mentioned information is urgent and a prompt reply is anticipated."),
        {"id": "sp2", "type": "spacer", "lines": 1},
        {"id": "table", "type": "ip_table"},
        {"id": "sp3", "type": "spacer", "lines": 1},
        _t("sig", "{officer_name}\n{officer_designation}\n{officer_location}\n"
                  "Contact No.: {officer_contact}\nDated : {letter_date}"),
    ],
}
