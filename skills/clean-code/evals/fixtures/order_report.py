import sys

# fee
F = 0.02


def proc(d, flag):
    # this function processes the orders and returns the results
    res = []
    for o in d:
        if o != None:
            if o.get("status") == "A":
                if o.get("total") != None:
                    if o["total"] > 0:
                        t = o["total"]
                        disc = 0
                        if t > 100:
                            disc = t * 0.15
                        net = t - disc
                        fee = net * 0.02
                        res.append({"id": o["id"], "net": round(net - fee, 2)})
    if flag:
        res = sorted(res, key=lambda x: x["net"], reverse=True)
    return res


def proc2(d, flag):
    # same as proc but for the pending ones
    res = []
    for o in d:
        if o != None:
            if o.get("status") == "P":
                if o.get("total") != None:
                    if o["total"] > 0:
                        t = o["total"]
                        disc = 0
                        if t > 100:
                            disc = t * 0.15
                        net = t - disc
                        fee = net * 0.02
                        res.append({"id": o["id"], "net": round(net - fee, 2)})
    if flag:
        res = sorted(res, key=lambda x: x["net"], reverse=True)
    return res


def days_old(ts, now):
    try:
        return int((now - ts) / 86400)
    except:
        pass
    return 0


# def old_proc(d):
#     out = []
#     for x in d:
#         if x["status"] == "A":
#             out.append(x["id"])
#     return out


if __name__ == "__main__":
    orders = [
        {"id": "o-1", "status": "A", "total": 250.0},
        {"id": "o-2", "status": "P", "total": 40.0},
        {"id": "o-3", "status": "A", "total": 80.0},
        None,
        {"id": "o-4", "status": "A", "total": 0},
        {"id": "o-5", "status": "P", "total": 120.0},
        {"id": "o-6", "status": "X", "total": 99.0},
        {"id": "o-7", "status": "A", "total": None},
    ]
    for row in proc(orders, True):
        print(row["id"], row["net"])
    for row in proc2(orders, True):
        print(row["id"], row["net"])
    print(days_old(1700000000, 1700432000))
