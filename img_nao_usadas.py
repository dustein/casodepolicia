import os
from bs4 import BeautifulSoup
import re


def listar_imagens_usadas(pasta):
    """
    Analisa todos os arquivos HTML na pasta e extrai as imagens
    que estão sendo referenciadas na pasta uploads (com diferentes padrões)
    """
    imagens_usadas = set()
    
    print("=== DEBUG: Analisando arquivos HTML ===")
    
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.html'):
            caminho_arquivo = os.path.join(pasta, arquivo)
            print(f"\n📄 Analisando: {arquivo}")
            
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    soup = BeautifulSoup(conteudo, 'html.parser')
                    
                    # Encontra todas as tags <img>
                    imgs_encontradas = soup.find_all('img')
                    print(f"   Encontradas {len(imgs_encontradas)} tags <img>")
                    
                    for img in imgs_encontradas:
                        src = img.get('src', '')
                        print(f"   → src encontrado: '{src}'")
                        
                        # Padrões mais flexíveis para detectar uploads
                        padroes_uploads = [
                            r'/uploads/',      # /uploads/imagem.jpg
                            r'uploads/',       # uploads/imagem.jpg  
                            r'\\uploads\\',    # \uploads\imagem.jpg (Windows)
                            r'\.?/?uploads/',  # ./uploads/ ou ../uploads/
                        ]
                        
                        for padrao in padroes_uploads:
                            if re.search(padrao, src, re.IGNORECASE):
                                # Extrai apenas o nome do arquivo
                                nome_imagem = os.path.basename(src)
                                if nome_imagem:  # Verifica se não está vazio
                                    imagens_usadas.add(nome_imagem)
                                    print(f"   ✅ Imagem adicionada: '{nome_imagem}'")
                                break
                        else:
                            print(f"   ❌ Src não corresponde aos padrões de uploads")
                            
            except Exception as e:
                print(f"   ⚠️ Erro ao processar arquivo {arquivo}: {e}")
    
    print(f"\n📊 Total de imagens únicas encontradas: {len(imagens_usadas)}")
    return imagens_usadas


def listar_imagens_da_pasta_uploads(pasta_uploads):
    """
    Lista todos os arquivos de imagem na pasta uploads
    """
    extensoes_imagem = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
    imagens = set()
    
    if not os.path.exists(pasta_uploads):
        print(f"⚠️ Pasta uploads não encontrada: {pasta_uploads}")
        return imagens
    
    print(f"\n📁 Verificando pasta: {pasta_uploads}")
    
    for arquivo in os.listdir(pasta_uploads):
        caminho_completo = os.path.join(pasta_uploads, arquivo)
        if os.path.isfile(caminho_completo):
            _, extensao = os.path.splitext(arquivo.lower())
            if extensao in extensoes_imagem:
                imagens.add(arquivo)
                print(f"   📸 Imagem encontrada: {arquivo}")
    
    print(f"📊 Total de imagens na pasta uploads: {len(imagens)}")
    return imagens


def confirmar_delecao(imagens_nao_usadas):
    """
    Solicita confirmação antes de deletar as imagens
    """
    if not imagens_nao_usadas:
        return False
    
    print(f"\n⚠️  ATENÇÃO: {len(imagens_nao_usadas)} imagens serão DELETADAS permanentemente!")
    print("Imagens que serão deletadas:")
    for imagem in sorted(imagens_nao_usadas):
        print(f"   🗑️  {imagem}")
    
    resposta = input("\nDeseja continuar com a deleção? (s/N): ").lower().strip()
    return resposta in ['s', 'sim', 'y', 'yes']


def deletar_imagens_nao_usadas(pasta_uploads, imagens_nao_usadas):
    """
    Deleta as imagens não utilizadas
    """
    imagens_deletadas = []
    erros_delecao = []
    
    print(f"\n🗑️  Iniciando deleção de {len(imagens_nao_usadas)} imagens...")
    
    for imagem in imagens_nao_usadas:
        caminho_imagem = os.path.join(pasta_uploads, imagem)
        try:
            # Verifica se o arquivo ainda existe
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
                imagens_deletadas.append(imagem)
                print(f"   ✅ Deletada: {imagem}")
            else:
                print(f"   ⚠️  Arquivo não encontrado: {imagem}")
        except Exception as e:
            erros_delecao.append((imagem, str(e)))
            print(f"   ❌ Erro ao deletar {imagem}: {e}")
    
    print(f"\n📊 Resumo da deleção:")
    print(f"   ✅ Imagens deletadas com sucesso: {len(imagens_deletadas)}")
    print(f"   ❌ Erros na deleção: {len(erros_delecao)}")
    
    return imagens_deletadas, erros_delecao


def main():
    """
    Função principal que executa a análise e deleção
    """
    # Obtém a pasta onde o script está localizado
    pasta_atual = os.path.dirname(os.path.abspath(__file__))
    pasta_uploads = os.path.join(pasta_atual, 'uploads')
    
    print(f"🔍 Analisando arquivos HTML em: {pasta_atual}")
    print(f"📂 Verificando imagens em: {pasta_uploads}")
    print("=" * 60)
    
    # Lista as imagens usadas nos arquivos HTML
    imagens_usadas = listar_imagens_usadas(pasta_atual)
    
    # Lista as imagens na pasta uploads
    imagens_na_pasta = listar_imagens_da_pasta_uploads(pasta_uploads)
    
    # Encontra as imagens não utilizadas
    imagens_nao_usadas = imagens_na_pasta - imagens_usadas
    
    print("\n" + "=" * 60)
    print("📋 RESULTADO DA ANÁLISE:")
    print("=" * 60)
    
    if imagens_nao_usadas:
        print(f"🗑️  Encontradas {len(imagens_nao_usadas)} imagens NÃO UTILIZADAS:")
        for imagem in sorted(imagens_nao_usadas):
            print(f"   • {imagem}")
    else:
        print("✅ Todas as imagens na pasta uploads estão sendo utilizadas!")
        return []
    
    if imagens_usadas:
        print(f"\n✅ Imagens UTILIZADAS ({len(imagens_usadas)}):")
        for imagem in sorted(imagens_usadas):
            print(f"   • {imagem}")
    
    # Solicita confirmação e deleta as imagens
    if confirmar_delecao(imagens_nao_usadas):
        imagens_deletadas, erros = deletar_imagens_nao_usadas(pasta_uploads, imagens_nao_usadas)
        
        # Salva o log das imagens deletadas
        with open('imagens_deletadas_log.txt', 'w', encoding='utf-8') as f:
            f.write("=== LOG DE IMAGENS DELETADAS ===\n\n")
            f.write(f"Data/Hora: {os.popen('date').read().strip()}\n")
            f.write(f"Total de imagens deletadas: {len(imagens_deletadas)}\n\n")
            f.write("Imagens deletadas:\n")
            for imagem in sorted(imagens_deletadas):
                f.write(f"- {imagem}\n")
            
            if erros:
                f.write(f"\nErros na deleção ({len(erros)}):\n")
                for imagem, erro in erros:
                    f.write(f"- {imagem}: {erro}\n")
        
        print(f"\n💾 Log salvo em: imagens_deletadas_log.txt")
        return imagens_deletadas
    else:
        print("\n❌ Deleção cancelada pelo usuário.")
        
        # Salva apenas a lista das imagens não utilizadas
        with open('imagens_nao_utilizadas.txt', 'w', encoding='utf-8') as f:
            f.write("Imagens não utilizadas (não deletadas):\n")
            for imagem in sorted(imagens_nao_usadas):
                f.write(f"{imagem}\n")
        
        print(f"💾 Lista salva em: imagens_nao_utilizadas.txt")
        return []


if __name__ == '__main__':
    imagens_deletadas = main()
    
    if imagens_deletadas:
        print(f"\n🎉 Processo concluído! {len(imagens_deletadas)} imagens foram deletadas.")
    else:
        print(f"\n✅ Processo concluído sem deleções.")
