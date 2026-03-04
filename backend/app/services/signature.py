def build_signature(workspace) -> str:
    name = (workspace.signature_name or "").strip()
    company = (workspace.company_display_name or workspace.name or "MailMind").strip()
    email = (workspace.company_email or "").strip()
    address = (workspace.company_address or "").strip()
    phone = (workspace.company_phone or "").strip()
    style = (workspace.signature_style or "team").strip().lower()

    lines = []

    # Main line
    if style == "name" and name:
        lines.append(name)
        lines.append(company)
    elif style == "minimal":
        lines.append(company)
    else:
        # default "team"
        lines.append(f"The {company} Team")

    # Contact block
    if email:
        lines.append(email)
    if phone:
        lines.append(phone)
    if address:
        lines.append(address)

    return "\n".join(lines).strip()