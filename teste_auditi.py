import pdfplumber
import re

def obter_itens(caminho_pdf="teste_auditi.pdf"):
    dados = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()

            if not texto:
                continue

            linhas = texto.split("\n")

            i = 0
            while i < len(linhas):
                linha = linhas[i].strip()

                # ignora linhas vazias
                if not linha:
                    i += 1
                    continue

                # procura quantidade (ex: 1.234,56)
                match_qtd = re.search(r"(\d{1,3}(?:\.\d{3})*,\d+)", linha)

                if match_qtd:
                    quantidade = match_qtd.group(1)

                    # 🔥 corta para 2 casas decimais
                    if "," in quantidade:
                        parte_int, parte_dec = quantidade.split(",")
                        quantidade = f"{parte_int},{parte_dec[:2]}"

                    # remove quantidade da linha
                    resto = linha[:match_qtd.start()].strip()
                    partes = resto.split()

                    if len(partes) > 1:
                        codigo = partes[0]
                        descricao = " ".join(partes[1:])

                        # limpeza básica
                        descricao = descricao.replace(" - ", " ").strip()

                        # 🔥 CAPTURA UNIDADE (ao invés de remover)
                        unidade = None
                        match_un = re.search(r"\b(M2|KG|UN|MT|PC|PR)\b$", descricao)

                        if match_un:
                            unidade = match_un.group(1)
                            descricao = descricao.replace(unidade, "").strip()

                        endereco = None

                        # 🔥 verifica próxima linha (ENDEREÇO)
                        if i + 1 < len(linhas):
                            prox_linha = linhas[i + 1].strip()

                            if "ENDEREÇO" in prox_linha.upper():
                                endereco = prox_linha.replace("ENDEREÇO:", "").strip()
                                i += 1

                        dados.append({
                            "codigo": codigo,
                            "descricao": descricao,
                            "quantidade": quantidade,
                            "endereco": endereco,
                            "unidade": unidade  # 👈 NOVO CAMPO
                        })

                i += 1

    return dados


# 🔹 modo teste
if __name__ == "__main__":
    itens = obter_itens()

    for item in itens:
        print(item)