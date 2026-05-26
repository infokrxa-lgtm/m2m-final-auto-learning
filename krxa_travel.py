def detect_intent(text, service="free"):
    t = text.lower()

    if any(x in text for x in ["역", "어디", "길", "지도", "가는", "가나요"]):
        return "map"
    if any(x in t for x in ["where", "station", "map", "direction", "how can i get"]):
        return "map"

    if any(x in text for x in ["맛집", "식당", "카페", "먹", "메뉴", "예약", "가격"]):
        return "food"
    if any(x in t for x in ["restaurant", "food", "eat", "cafe", "menu", "reservation", "recommend"]):
        return "food"

    if any(x in text for x in ["숙소", "호텔", "체크인"]):
        return "hotel"
    if any(x in t for x in ["hotel", "check in"]):
        return "hotel"

    return service


def get_cards(text, service="free"):
    intent = detect_intent(text, service)
    t = text.lower()
    cards = []

    if intent == "food":
        if any(x in text for x in ["맛집", "식당", "먹"]) or any(x in t for x in ["restaurant", "food", "eat"]):
            cards.append({
                "label": "근처 맛집 보기",
                "url": "https://www.google.com/maps/search/restaurant+near+me"
            })

        if "예약" in text or "reservation" in t or "book" in t:
            cards.append({
                "label": "예약 문장",
                "text": "Can I make a reservation?"
            })

        if "메뉴" in text or "추천" in text or "recommend" in t:
            cards.append({
                "label": "추천 메뉴 질문",
                "text": "What do you recommend here?"
            })

        if "가격" in text or "얼마" in text or "price" in t:
            cards.append({
                "label": "가격 질문",
                "text": "How much is it?"
            })

        return cards

    if intent == "map":
        cards.append({
            "label": "지도 열기",
            "url": "https://www.google.com/maps"
        })

        if "역" in text or "station" in t:
            cards.append({
                "label": "가까운 역 찾기",
                "url": "https://www.google.com/maps/search/station+near+me"
            })

        return cards

    if intent == "hotel":
        if "체크인" in text or "check in" in t:
            cards.append({
                "label": "체크인 문장",
                "text": "I would like to check in."
            })

        cards.append({
            "label": "숙소 찾기",
            "url": "https://www.google.com/maps/search/hotel+near+me"
        })

        return cards

    return []
