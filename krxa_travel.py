def get_cards(text):
    if "맛집" in text:
        return [
            {"label": "근처 맛집 보기", "url": "https://www.google.com/maps/search/restaurant"},
            {"label": "예약 문장", "text": "Can I make a reservation?"}
        ]

    if "길" in text:
        return [
            {"label": "지도 열기", "url": "https://www.google.com/maps"},
            {"label": "길 물어보기", "text": "How can I get there?"}
        ]

    return []
