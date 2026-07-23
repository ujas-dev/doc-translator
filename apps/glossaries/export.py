import xml.etree.ElementTree as ET
from xml.dom import minidom


def export_tbx(glossary):
    """Export glossary to TBX (TermBase eXchange) format."""
    tbx = ET.Element("tbx", {
        "type": "TBX",
        "datatype": "TBX",
        "xml:lang": glossary.target_lang,
    })

    header = ET.SubElement(tbx, "tbxHeader")
    meta = ET.SubElement(header, "meta")
    ET.SubElement(meta, "name").text = glossary.name
    ET.SubElement(meta, "sourceLang").text = glossary.source_lang
    ET.SubElement(meta, "targetLang").text = glossary.target_lang

    body = ET.SubElement(tbx, "body")

    for entry in glossary.entries.all():
        concept = ET.SubElement(body, "conceptEntry", {
            "id": str(entry.pk),
        })

        lang_set = ET.SubElement(concept, "langSet", {
            "xml:lang": glossary.source_lang,
        })
        tig = ET.SubElement(lang_set, "tig")
        term = ET.SubElement(tig, "term")
        term.text = entry.source

        lang_set2 = ET.SubElement(concept, "langSet", {
            "xml:lang": glossary.target_lang,
        })
        tig2 = ET.SubElement(lang_set2, "tig")
        term2 = ET.SubElement(tig2, "term")
        term2.text = entry.target

        if entry.context:
            note = ET.SubElement(tig2, "note")
            note.text = entry.context

    rough_string = ET.tostring(tbx, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)


def export_xliff(glossary):
    """Export glossary to XLIFF (XML Localization Interchange File Format)."""
    xliff = ET.Element("xliff", {
        "version": "1.2",
        "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
    })

    file_elem = ET.SubElement(xliff, "file", {
        "source-language": glossary.source_lang,
        "target-language": glossary.target_lang,
        "datatype": "plaintext",
        "original": glossary.name,
    })

    body = ET.SubElement(file_elem, "body")

    for entry in glossary.entries.all():
        trans_unit = ET.SubElement(body, "trans-unit", {
            "id": str(entry.pk),
        })

        source = ET.SubElement(trans_unit, "source")
        source.text = entry.source

        target = ET.SubElement(trans_unit, "target")
        target.text = entry.target

        if entry.context:
            note = ET.SubElement(trans_unit, "note")
            note.text = entry.context

    rough_string = ET.tostring(xliff, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)
