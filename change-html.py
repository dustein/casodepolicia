import os

# Código antigo e novo
codigo_antigo = '''<img class="header-img" src="caso_de_policia.jpg" alt="">'''

codigo_novo = '''<a href="/"><img class="header-img" src="caso_de_policia.jpg" alt="Header Caso de Polícia"></a>'''

# Processar todos os arquivos HTML do diretório atual
arquivos_modificados = 0

for arquivo in os.listdir('.'):
    if arquivo.endswith('.html'):
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        if codigo_antigo in conteudo:
            novo_conteudo = conteudo.replace(codigo_antigo, codigo_novo)
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(novo_conteudo)
            arquivos_modificados += 1
            print(f"Modificado: {arquivo}")

print(f"Total de arquivos modificados: {arquivos_modificados}")
