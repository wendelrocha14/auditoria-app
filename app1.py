from flask import Flask, render_template, request, redirect, session, send_file
from teste_auditi import obter_itens
from datetime import datetime
import csv
import os

app = Flask(__name__)
app.secret_key = "segredo123"

# Caminhos de arquivos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "teste_auditi.pdf")

# 🔵 HOME - Carregar o PDF do dia
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files.get("relatorio")
        if file:
            file.save(PDF_PATH)
            return redirect("/iniciar_auditoria")
    return render_template("home.html")

# 🟡 INICIAR AUDITORIA - Coleta os dados gerais
@app.route("/iniciar_auditoria", methods=["GET", "POST"])
def iniciar_auditoria():
    if request.method == "POST":
        # Salva as informações preenchidas na sessão para usar no final
        session["dados_auditoria"] = {
            "data": request.form.get("data"),
            "hora_inicio": request.form.get("hora_inicio"),
            "grupo": request.form.get("grupo"),
            "empresa": request.form.get("empresa"),
            "id": request.form.get("id")
        }
        return redirect("/itens")
    return render_template("iniciar_auditoria.html")

# 🟠 SELECIONAR ITENS - Lê o PDF e mostra a lista
@app.route("/itens", methods=["GET", "POST"])
def selecionar():
    if not os.path.exists(PDF_PATH):
        return "Erro: PDF não encontrado. Volte ao início."
    
    itens = obter_itens(PDF_PATH)

    if request.method == "POST":
        selecionados = []
        for i, item in enumerate(itens):
            if request.form.get(f"sel_{i}") == "on":
                selecionados.append(item)
        session["itens_selecionados"] = selecionados
        return redirect("/auditoria")
    return render_template("selecionar.html", itens=itens)

# 🔴 AUDITORIA E DOWNLOAD DO CSV
# 🔴 AUDITORIA E DOWNLOAD DO CSV
@app.route("/auditoria", methods=["GET", "POST"])
def auditoria():
    itens = session.get("itens_selecionados", [])
    dados = session.get("dados_auditoria", {})

    if request.method == "POST":
        # Pega a hora de fim que você digitou na tela
        hora_fim_digitada = request.form.get("hora_fim")
        
        resultado = []
        for i, item in enumerate(itens):
            qtd_real = request.form.get(f"qtd_{i}") or item["quantidade"]
            resultado.append({
                "codigo": item["codigo"],
                "descricao": item["descricao"],
                "unidade": item.get("unidade", "-"),
                "qtd_sistema": item["quantidade"],
                "qtd_real": qtd_real
            })

        nome_csv = f"auditoria_{dados.get('id', 'sem_id')}.csv"
        caminho_csv = os.path.join(BASE_DIR, nome_csv)

        with open(caminho_csv, mode="w", newline="", encoding="utf-8-sig") as arquivo:
            writer = csv.writer(arquivo, delimiter=";")
            writer.writerow(["Data", "Grupo", "Emp", "Código", "Material", "Un. Medida", "Estoque", "Físico", "idAudit", "hora inicio", "hora fim"])
            
            for r in resultado:
                writer.writerow([
                    dados.get("data"),
                    dados.get("grupo"),
                    dados.get("empresa"),
                    r["codigo"],
                    r["descricao"],
                    r["unidade"],
                    r["qtd_sistema"],
                    r["qtd_real"],
                    dados.get("id"),
                    dados.get("hora_inicio"),
                    hora_fim_digitada  # Agora usa a hora que você preencheu
                ])

        return send_file(caminho_csv, as_attachment=True)

    return render_template("auditoria.html", itens=itens, dados=dados)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
