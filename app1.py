from flask import Flask, render_template, request, redirect, session, send_file

from teste_auditi import obter_itens
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font
import csv
import os

app = Flask(__name__)
app.secret_key = "segredo123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_PATH = os.path.join(BASE_DIR, "teste_auditi.pdf")


# 🔵 HOME
@app.route("/")
def home():
    return render_template("home.html")


# 🟡 INICIAR AUDITORIA
@app.route("/iniciar_auditoria", methods=["GET", "POST"])
def iniciar_auditoria():

    if request.method == "POST":

        # salva dados iniciais
        session["dados_auditoria"] = {
            "data": request.form.get("data"),
            "hora_inicio": request.form.get("hora_inicio"),
            "grupo": request.form.get("grupo"),
            "empresa": request.form.get("empresa"),
            "id": request.form.get("id")
        }

        return redirect("/itens")

    return render_template("iniciar_auditoria.html")


# 🟠 SELECIONAR ITENS
@app.route("/itens", methods=["GET", "POST"])
def selecionar():

    itens = obter_itens(PDF_PATH)

    if request.method == "POST":

        selecionados = []

        for i, item in enumerate(itens):

            marcado = request.form.get(f"sel_{i}")

            if marcado == "on":
                selecionados.append(item)

        session["itens_selecionados"] = selecionados

        return redirect("/auditoria")

    return render_template(
        "selecionar.html",
        itens=itens
    )


# 🔴 AUDITORIA
@app.route("/auditoria", methods=["GET", "POST"])
def auditoria():

    itens = session.get("itens_selecionados", [])

    dados_auditoria = session.get("dados_auditoria", {})

    if request.method == "POST":

        resultado = []

        for i, item in enumerate(itens):

            # status do card
            status = request.form.get(f"status_{i}")

            # quantidade digitada
            qtd_real = request.form.get(f"qtd_{i}")

            # se vazio usa quantidade sistema
            if not qtd_real:
                qtd_real = item["quantidade"]

            # verifica divergência
            divergente = (
                str(qtd_real).strip()
                !=
                str(item["quantidade"]).strip()
            )

            resultado.append({

                "codigo": item["codigo"],

                "descricao": item["descricao"],

                "endereco": item.get("endereco", "-"),

                "unidade": item.get("unidade", "-"),

                "qtd_sistema": item["quantidade"],

                "qtd_real": qtd_real,

                "status": status,

                "divergente": divergente

            })

        # salva hora final
        dados_auditoria["hora_fim"] = datetime.now().strftime("%H:%M")

        print("\n===== DADOS AUDITORIA =====")
        print(dados_auditoria)

        print("\n===== RESULTADO AUDITORIA =====")

        for r in resultado:
            print(r)

        # salva resultado sessão
        session["resultado_auditoria"] = resultado

        # =========================
        # CRIA PASTA
        # =========================

        os.makedirs("auditorias", exist_ok=True)

        # pega id auditoria
        id_auditoria = dados_auditoria.get("id", "sem_id")

        # =========================
        # GERAR CSV
        # =========================

        nome_csv = f"auditorias/auditoria_{id_auditoria}.csv"

        with open(
            nome_csv,
            mode="w",
            newline="",
            encoding="utf-8-sig"
        ) as arquivo:

            # separador excel brasil
            writer = csv.writer(arquivo, delimiter=";")

            # cabeçalho
            writer.writerow([
                "Data",
                "Grupo",
                "Emp",
                "Código",
                "Material",
                "Un. Medida",
                "Estoque",
                "Físico",
                "idAudit",
                "hora inicio",
                "hora fim"
            ])

            # linhas
            for r in resultado:

                writer.writerow([

                    dados_auditoria.get("data"),

                    dados_auditoria.get("grupo"),

                    dados_auditoria.get("empresa"),

                    r["codigo"],

                    r["descricao"],

                    r["unidade"],

                    r["qtd_sistema"],

                    r["qtd_real"],

                    dados_auditoria.get("id"),

                    dados_auditoria.get("hora_inicio"),

                    dados_auditoria.get("hora_fim")

                ])

        print(f"\nCSV salvo em: {nome_csv}")

        # =========================
        # GERAR XLSX
        # =========================

        wb = Workbook()

        ws = wb.active

        ws.title = "Auditoria"

        # cabeçalhos
        headers = [
            "Data",
            "Grupo",
            "Emp",
            "Código",
            "Material",
            "Un. Medida",
            "Estoque",
            "Físico",
            "idAudit",
            "hora inicio",
            "hora fim"
        ]

        ws.append(headers)

        # deixa cabeçalho negrito
        for cell in ws[1]:
            cell.font = Font(bold=True)

        # adiciona linhas
        for r in resultado:

            ws.append([

                dados_auditoria.get("data"),

                dados_auditoria.get("grupo"),

                dados_auditoria.get("empresa"),

                r["codigo"],

                r["descricao"],

                r["unidade"],

                r["qtd_sistema"],

                r["qtd_real"],

                dados_auditoria.get("id"),

                dados_auditoria.get("hora_inicio"),

                dados_auditoria.get("hora_fim")

            ])

        # largura colunas
        larguras = {
            "A": 15,
            "B": 20,
            "C": 20,
            "D": 15,
            "E": 45,
            "F": 15,
            "G": 12,
            "H": 12,
            "I": 15,
            "J": 15,
            "K": 15
        }

        for coluna, largura in larguras.items():
            ws.column_dimensions[coluna].width = largura

        # salva excel
          # salva excel
        nome_xlsx = f"auditorias/auditoria_{id_auditoria}.xlsx"

        wb.save(nome_xlsx)

        print(f"\nXLSX salvo em: {nome_xlsx}")

        # AGORA FICOU ASSIM:
        return send_file(nome_xlsx, as_attachment=True)

    return render_template(
        "auditoria.html",
        itens=itens,
        dados=dados_auditoria
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
