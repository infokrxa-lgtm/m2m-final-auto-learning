def get_cards(text, service="free"):
    t = text.lower()
    cards = []

    if service == "food":
        if "맛집" in text or "restaurant" in t or "eat" in t or "food" in t:
            cards.append({"label": "근처 맛집 보기", "url": "https://www.google.com/maps/search/restaurant+near+me"})
        if "예약" in text or "reservation" in t or "book" in t:
            cards.append({"label": "예약 문장", "text": "Can I make a reservation?"})
        if "메뉴" in text or "recommend" in t or "추천" in text:
            cards.append({"label": "추천 메뉴 질문", "text": "What do you recommend here?"})
        if "가격" in text or "price" in t or "얼마" in text:
            cards.append({"label": "가격 질문", "text": "How much is it?"})
        if not cards:
            cards.append({"label": "맛집 질문", "text": "Could you recommend a good restaurant nearby?"})
        return cards

    if service == "map":
        if "길" in text or "어디" in text or "where" in t or "direction" in t:
            cards.append({"label": "지도 열기", "url": "https://www.google.com/maps"})
        if "역" in text or "station" in t:
            cards.append({"label": "가까운 역 찾기", "url": "https://www.google.com/maps/search/station+near+me"})
        if not cards:
            cards.append({"label": "길 묻기", "text": "How can I get there?"})
        return cards

    if service == "hotel":
        if "체크인" in text or "check in" in t:
            cards.append({"label": "체크인 문장", "text": "I would like to check in."})
        if "예약" in text or "reservation" in t:
            cards.append({"label": "예약 확인", "text": "I have a reservation under this name."})
        if not cards:
            cards.append({"label": "숙소 찾기", "url": "https://www.google.com/maps/search/hotel+near+me"})
        return cards

    return []
