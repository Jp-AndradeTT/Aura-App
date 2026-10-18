"""Motor de cálculo: toda a matemática fica aqui (nunca na IA)."""
import math
from datetime import date

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes(k):
    h = date.today()
    n = h.month - 1 + k
    return f"{MESES[n % 12]}/{str(h.year + n // 12)[2:]}"


def _num(v, default=0.0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return default if x != x or abs(x) > 1e9 else x  # recusa NaN, infinito e números absurdos


def r2(v):
    return round(v, 2)


def _txt(v, n):
    """Texto seguro: sempre str, sem NUL nem caracteres inválidos, com tamanho limitado."""
    return v.encode("utf-8", "ignore").decode("utf-8").replace("\x00", "")[:n] if isinstance(v, str) else ""


def clean_items(raw):
    out = []
    for r in (raw[:300] if isinstance(raw, list) else []):
        if not isinstance(r, dict):
            continue
        t = min(max(0, int(_num(r.get("t")))), 999)
        a = max(0, min(int(_num(r.get("a"))), t))
        out.append({"d": _txt(r.get("d"), 80), "c": _txt(r.get("c"), 40) or "Outros", "v": r2(_num(r.get("v"))), "a": a, "t": t})
    return out


def clean_profile(raw):
    raw = raw if isinstance(raw, dict) else {}
    return {"renda": max(_num(raw.get("renda"), 1), 1.0),
            "fixos": max(_num(raw.get("fixos")), 0.0),
            "meta": min(max(_num(raw.get("meta"), 6), 0.0), 36.0),
            "venc": min(max(int(_num(raw.get("venc"), 10)), 1), 31)}


def analyze(items, profile, reserve_pct=60.0):
    frac = min(100.0, max(0.0, reserve_pct)) / 100
    par = [i for i in items if i["t"] > 0]
    total = sum(i["v"] for i in items)
    parcelado = sum(i["v"] for i in par)
    a_vista = total - parcelado

    cats = {}
    for i in items:
        cats[i["c"]] = cats.get(i["c"], 0) + i["v"]

    proj, acc = [], 0.0
    for k in range(7):
        p = sum(i["v"] for i in par if i["a"] + k <= i["t"])
        fat = p + a_vista
        sobra = profile["renda"] - profile["fixos"] - fat
        res = max(0.0, sobra * frac)
        if k > 0:
            acc += res
        proj.append({"k": k, "mes": mes(k), "parcelas": r2(p), "a_vista": r2(a_vista), "fatura": r2(fat),
                     "pct": round((profile["fixos"] + fat) / profile["renda"] * 100, 1),
                     "sobra": r2(sobra), "reserva": r2(res), "acumulado": r2(acc)})

    meta = profile["meta"] * profile["fixos"]
    mes_meta = None
    hit = next((x for x in proj if x["k"] > 0 and x["acumulado"] >= meta), None) if meta > 0 else None
    if hit:
        mes_meta = hit["mes"]
    elif meta > 0 and proj[6]["reserva"] > 0:
        mes_meta = mes(6 + math.ceil((meta - proj[6]["acumulado"]) / proj[6]["reserva"]))

    queda = next(({"mes": proj[k]["mes"], "fatura": proj[k]["fatura"],
                   "economia": r2(proj[k - 1]["fatura"] - proj[k]["fatura"])}
                  for k in range(1, 7) if proj[k]["parcelas"] < proj[k - 1]["parcelas"]), None)

    return {
        "total": r2(total), "parcelado": r2(parcelado), "a_vista": r2(a_vista),
        "pct_comprometido": proj[0]["pct"], "restante_parcelas": r2(sum(i["v"] * (i["t"] - i["a"]) for i in par)),
        "categorias": sorted(({"nome": k, "valor": r2(v)} for k, v in cats.items()), key=lambda x: -x["valor"]),
        "parcelas": [{"compra": i["d"], "parcela": f'{i["a"]}/{i["t"]}', "valor": i["v"], "restam": i["t"] - i["a"],
                      "saldo": r2(i["v"] * (i["t"] - i["a"])), "termina": mes(i["t"] - i["a"])} for i in par],
        "projecao": proj, "meta_reserva": r2(meta), "mes_meta": mes_meta, "queda": queda,
    }


def rule_plan(an, profile, reserve_pct):
    """Plano padrão por regras (usado sem IA ou se a IA falhar)."""
    p1, p0 = an["projecao"][1], an["projecao"][0]
    q = an["queda"]
    passos = [
        {"titulo": "Pague a fatura atual por inteiro", "valor": brl(an["total"]), "detalhes": [
            f'Vencimento no dia {profile["venc"]}: programe o pagamento com 2 dias de antecedência.',
            "Pague o valor total, não o mínimo, para evitar o rotativo (juros muito altos).",
            "Se faltar saldo, pague o máximo possível e negocie o restante antes de vencer."]},
        {"titulo": "Descubra sua sobra mensal real", "valor": brl(p0["sobra"]), "detalhes": [
            f'Renda {brl(profile["renda"])} − fixos {brl(profile["fixos"])} − fatura {brl(an["total"])} = {brl(p0["sobra"])}.',
            "Sobra negativa: o primeiro objetivo é cortar gastos até zerar o déficit." if p0["sobra"] < 0
            else "Esse é o dinheiro que alimenta o plano: trate-o como já comprometido."]},
        {"titulo": "Abra a caixinha da fatura", "valor": f'{brl(p1["parcelas"])}/mês', "detalhes": [
            "Crie uma conta ou cofrinho separado, com liquidez diária.",
            f'Todo mês, ao receber, transfira {brl(p1["parcelas"])}: são as parcelas já assumidas.',
            "Pague a fatura a partir dessa caixinha, sem usar o dinheiro do dia a dia."]},
        {"titulo": "Defina o teto do gasto à vista", "valor": f'{brl(an["a_vista"])}/mês', "detalhes": [
            f'Limite as compras à vista no cartão a {brl(an["a_vista"])} por mês.',
            f'Tente reduzir 10% ({brl(an["a_vista"] * 0.1)}) em lazer e alimentação fora de casa.']},
        {"titulo": "Construa a reserva de emergência", "valor": f'{brl(p1["reserva"])}/mês', "detalhes": [
            f'Meta: {brl(an["meta_reserva"])} ({profile["meta"]:g} meses de gastos fixos).',
            f'Transfira {reserve_pct:g}% da sobra ({brl(p1["reserva"])}) logo no início do mês.',
            f'Previsão de meta atingida: {an["mes_meta"]}.' if an["mes_meta"] else "Sem sobra no cenário atual: corte gastos antes de começar a guardar."]},
        {"titulo": "Pause novas parcelas", "valor": brl(profile["fixos"] * 3), "detalhes": [
            f'Evite novos parcelamentos até a reserva chegar a {brl(profile["fixos"] * 3)} (3 meses de fixos).',
            "Para compras grandes, junte o dinheiro antes e pague à vista."]},
        {"titulo": "Redirecione o que sair da fatura", "valor": q["mes"] if q else "—", "detalhes": [
            (f'Em {q["mes"]} a fatura cai para {brl(q["fatura"])}, economia de {brl(q["economia"])} por mês.' if q
             else "Quando uma parcela terminar, o valor fica livre."),
            "Mantenha o mesmo depósito na caixinha e envie a diferença para a reserva."]},
        {"titulo": "Faça a revisão mensal", "valor": "10 min", "detalhes": [
            "Compare a fatura real com a projetada e atualize renda e gastos fixos.",
            "Confirme se os depósitos da caixinha e da reserva foram feitos."]},
    ]
    nivel = "alto" if an["pct_comprometido"] > 70 else "moderado" if an["pct_comprometido"] > 50 else "saudável"
    return {"diagnostico": f'Sua renda está {an["pct_comprometido"]:.0f}% comprometida (nível {nivel}), com {brl(an["restante_parcelas"])} ainda a pagar em parcelas.',
            "alertas": ["Sua sobra mensal está negativa. Priorize cortes e evite novas parcelas."] if p0["sobra"] < 0 else [],
            "passos": passos}
