def get_cards(text, service="free"):
    if service == "food" or "맛집" in text or "restaurant" in text.lower() or "food" in text.lower():
        return [
            {"label": "근처 맛집 보기", "url": "https://www.google.com/maps/search/restaurant"},
            {"label": "예약 문장", "text": "Can I make a reservation?"}
        ]

    if service == "map" or "길" in text or "where" in text.lower() or "station" in text.lower():
        return [
            {"label": "지도 열기", "url": "https://www.google.com/maps"},
            {"label": "길 물어보기", "text": "How can I get there?"}
        ]

    return []
