"""Planilha detalhada. Todos os valores vêm do cálculo do app (nada é recalculado aqui)."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .calculator import mes

MONEY = '"R$" #,##0.00'
HEAD = PatternFill("solid", fgColor="14213D")
SOFT = PatternFill("solid", fgColor="E4EBFA")
LINE = Border(bottom=Side(style="thin", color="D5DBE5"))


def _level(p):
    return PatternFill("solid", fgColor="DFF3E9" if p <= 50 else "FDF1D6" if p <= 70 else "FBE6E2")


def _table(wb, title, subtitle, header, rows, money=(), pct=(), total=None, wrap=()):
    ws = wb.create_sheet(title)
    ws["A1"], ws["A2"] = title, subtitle
    ws["A1"].font, ws["A2"].font = Font(bold=True, size=15, color="14213D"), Font(italic=True, color="5B667C")
    ws.append([])
    ws.append(header)
    for c in ws[4]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), HEAD
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for r in rows:
        ws.append(r)
    if total:
        ws.append(total)
        for c in ws[ws.max_row]:
            c.font, c.fill = Font(bold=True), SOFT
    for row in ws.iter_rows(min_row=5):
        for c in row:
            c.border = LINE
            if c.column_letter in money:
                c.number_format = MONEY
            if c.column_letter in pct:
                c.number_format = '0"%"'
            if c.column_letter in wrap:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    for col in ws.columns:
        w = max(len(str(c.value or "")) for c in col[3:]) if ws.max_row > 3 else 10
        ws.column_dimensions[col[0].column_letter].width = min(70, max(13, w + 3))
    ws.freeze_panes = "A5"
    return ws


def build_workbook(inv, history):
    an, plan, prof, items = inv["analysis"], inv["plan"], inv["profile"], inv["items"]
    proj = an["projecao"]
    wb = Workbook()
    wb.remove(wb.active)

    # 1. Resumo
    sobra = proj[0]["sobra"]
    rows = [
        ["Fatura", inv["label"], inv.get("bank") or "", None],
        ["Total da fatura", an["total"], "Soma de todos os lançamentos", "m"],
        ["Parcelado", an["parcelado"], "Parcelas que se repetem nos próximos meses", "m"],
        ["À vista", an["a_vista"], "Compras sem parcelamento", "m"],
        ["Renda mensal líquida", prof["renda"], "Informada por você", "m"],
        ["Gastos fixos", prof["fixos"], "Informados por você", "m"],
        ["Sobra do mês (renda − fixos − fatura)", sobra, "Negativa = orçamento no vermelho", "m"],
        ["Renda comprometida", an["pct_comprometido"], "Fixos + fatura sobre a renda", "p"],
        ["Saldo futuro em parcelas", an["restante_parcelas"], "Total ainda a pagar das parcelas atuais", "m"],
        ["Meta de reserva", an["meta_reserva"], f'{prof["meta"]:g} meses de gastos fixos', "m"],
        ["Meta atingida em", an["mes_meta"] or "Sem sobra suficiente", f'Guardando {inv["reserve_pct"]:g}% da sobra', None],
        ["Caixinha da fatura (por mês)", proj[1]["parcelas"], f'Parcelas já assumidas para {proj[1]["mes"]}', "m"],
        ["Reserva sugerida (por mês)", proj[1]["reserva"], "Parte da sobra a guardar", "m"],
        ["Próxima queda da fatura", (an["queda"] or {}).get("mes", "—"),
         f'Economia de R$ {an["queda"]["economia"]:,.2f}/mês' if an["queda"] else "Nenhuma parcela termina em 6 meses", None],
    ]
    ws = _table(wb, "Resumo", plan.get("diagnostico", ""), ["Indicador", "Valor", "Leitura"], [r[:3] for r in rows])
    for n, r in enumerate(rows, 5):
        ws[f"B{n}"].number_format = MONEY if r[3] == "m" else '0.0"%"' if r[3] == "p" else "General"
        ws[f"B{n}"].alignment = Alignment(horizontal="right")
    ws["B12"].fill = _level(an["pct_comprometido"])

    # 2. Lançamentos
    _table(wb, "Lançamentos", "Itens da fatura conferidos por você",
           ["Descrição", "Categoria", "Valor", "Parcela atual", "Total de parcelas", "Tipo"],
           [[i["d"], i["c"], i["v"], i["a"], i["t"], "Parcelado" if i["t"] else "À vista"] for i in items],
           money=("C",), total=["Total", "", an["total"], "", "", ""])

    # 3. Categorias
    _table(wb, "Categorias", "Onde o dinheiro da fatura foi",
           ["Categoria", "Valor", "% da fatura"],
           [[c["nome"], c["valor"], round(c["valor"] / an["total"] * 100, 1) if an["total"] else 0] for c in an["categorias"]],
           money=("B",), pct=("C",), total=["Total", an["total"], 100])

    # 4. Parcelas
    _table(wb, "Parcelas", "Situação de cada compra parcelada",
           ["Compra", "Parcela", "Valor da parcela", "Restam", "Saldo a pagar", "Última parcela em"],
           [[p["compra"], p["parcela"], p["valor"], p["restam"], p["saldo"], p["termina"]] for p in an["parcelas"]],
           money=("C", "E"), total=["Total", "", sum(p["valor"] for p in an["parcelas"]), "", an["restante_parcelas"], ""])

    # 5. Parcelas por mês (matriz)
    par = [i for i in items if i["t"] > 0]
    matrix = [[i["d"]] + [i["v"] if i["a"] + k <= i["t"] else 0 for k in range(7)] for i in par]
    _table(wb, "Parcelas por mês", "Quanto cada compra pesa em cada fatura (0 = já quitada)",
           ["Compra"] + [mes(k) for k in range(7)], matrix, money=tuple("BCDEFGH"),
           total=["Total de parcelas"] + [x["parcelas"] for x in proj])

    # 6. Projeção
    ws = _table(wb, "Projeção", "Estimativa assumindo gastos à vista iguais aos desta fatura",
                ["Mês", "Parcelas", "À vista (est.)", "Fatura estimada", "% da renda", "Sobra", "Reserva sugerida", "Reserva acumulada", "% da meta"],
                [[x["mes"], x["parcelas"], x["a_vista"], x["fatura"], x["pct"], x["sobra"], x["reserva"], x["acumulado"],
                  min(100, round(x["acumulado"] / an["meta_reserva"] * 100)) if an["meta_reserva"] else 0] for x in proj],
                money=("B", "C", "D", "F", "G", "H"), pct=("I",))
    for n, x in enumerate(proj, 5):
        ws[f"E{n}"].number_format, ws[f"E{n}"].fill = '0.0"%"', _level(x["pct"])

    # 7. Plano de ação
    prow = [[n, p.get("titulo", ""), p.get("valor", ""), d, ""] for n, p in enumerate(plan["passos"], 1)
            for d in (p.get("detalhes") or [""])]
    ws = _table(wb, "Plano de ação", "Passo a passo para pagar as faturas e formar a reserva",
                ["Passo", "Título", "Valor-chave", "Ação", "Concluído?"], prow, wrap=("B", "D"))
    ws.column_dimensions["D"].width = 80

    # 8. Evolução (histórico do cliente)
    if history:
        _table(wb, "Evolução", "Suas faturas ao longo do tempo",
               ["Fatura", "Data", "Total", "Parcelado", "À vista", "% da renda", "Saldo futuro em parcelas"],
               [[h["label"], h["created_at"][:10], h["total"], h["parcelado"], h["a_vista"], h["pct"], h["restante"]] for h in history],
               money=("C", "D", "E", "G"), pct=("F",))
    for sheet in wb.worksheets:  # texto vindo da fatura/IA nunca pode virar fórmula (=, +, -, @)
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value[:1] in ("=", "+", "-", "@", "\t", "\r"):
                    cell.data_type, cell.quotePrefix = "s", True
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
