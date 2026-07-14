def render_chat_list(chats, chat_titles, active_chat):

    html = ""

    for cid in chats.keys():

        title = chat_titles.get(cid, cid)

        active = "active" if cid == active_chat else ""

        html += f"""
        <a class="chat-item {active}" href="/switch/{cid}">
            {title}
        </a>
        """

    return html