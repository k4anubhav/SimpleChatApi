from typing import TypedDict


class ConversationBrief(TypedDict):
    icon: str
    id: int
    inDay: bool
    isGroup: bool
    isOnline: bool
    lastMsg: str
    lastMsgID: int
    lastMsgTime: int
    title: str
    unread: int
    update: int
