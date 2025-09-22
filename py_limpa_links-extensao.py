#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para renomear arquivos HTML físicos após limpeza de links
Complementa o script anterior garantindo consistência entre links e arquivos
"""

import os
import re
import unicodedata
import shutil
from urllib.parse import unquote, urlparse
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from pathlib import Path


class FileRenamer:
    def __init__(self, folder_path):
        """
        Inicializa o renomeador de arquivos
        
        Args:
            folder_path (str): Caminho para a pasta contendo os arquivos
        """
        self.folder_path = Path(folder_path)
        self.index_file = self.folder_path / 'index.html'
        self.sitemap_file = self.folder_path / 'sitemap.xml'
        self.html_files = []
        self.rename_map = {}
        self.errors = []
        
    def remove_accents(self, text):
        """
        Remove acentos e normaliza texto para ASCII
        
        Args:
            text (str): Texto a ser normalizado
            
        Returns:
            str: Texto sem acentos
        """
        nfd = unicodedata.normalize('NFD', text)
        ascii_text = ''.join(c for c in nfd if unicodedata.combining(c) == 0)
        return ascii_text
    
    def clean_filename(self, filename):
        """
        Limpa nome de arquivo seguindo as mesmas regras dos links
        
        Args:
            filename (str): Nome do arquivo original
            
        Returns:
            str: Nome do arquivo limpo
        """
        # Separa nome e extensão
        name, ext = os.path.splitext(filename)
        
        # Remove acentos
        name = self.remove_accents(name)
        
        # Substitui espaços por hífens
        name = re.sub(r'\s+', '-', name)
        
        # Remove caracteres especiais, mantendo apenas alfanuméricos, hífens e underscores
        name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)
        
        # Remove múltiplos hífens consecutivos
        name = re.sub(r'-+', '-', name)
        
        # Remove hífens no início e fim
        name = name.strip('-')
        
        # Converte para minúsculas
        name = name.lower()
        
        return name + ext
    
    def extract_links_from_index(self):
        """
        Extrai links do index.html para mapear arquivos referenciados
        
        Returns:
            set: Conjunto de arquivos HTML referenciados
        """
        referenced_files = set()
        
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                soup = BeautifulSoup(content, 'html.parser')
                
                # Encontra todos os links <a href="">
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.endswith('.html'):
                        # Remove caminho e parâmetros, pega só o nome do arquivo
                        parsed = urlparse(href)
                        filename = os.path.basename(parsed.path)
                        if filename and filename != 'index.html':
                            referenced_files.add(filename)
                            
        except Exception as e:
            self.errors.append(f"Erro ao processar index.html: {e}")
            
        return referenced_files
    
    def extract_links_from_sitemap(self):
        """
        Extrai links do sitemap.xml para mapear arquivos referenciados
        
        Returns:
            set: Conjunto de arquivos HTML referenciados
        """
        referenced_files = set()
        
        try:
            if self.sitemap_file.exists():
                tree = ET.parse(self.sitemap_file)
                root = tree.getroot()
                
                # Define namespace se existir
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Tenta diferentes formatos de sitemap
                for url in root.findall('.//ns:loc', namespace):
                    if url.text and url.text.endswith('.html'):
                        parsed = urlparse(url.text)
                        filename = os.path.basename(parsed.path)
                        if filename and filename != 'index.html':
                            referenced_files.add(filename)
                
                # Se não encontrou com namespace, tenta sem
                if not referenced_files:
                    for url in root.findall('.//loc'):
                        if url.text and url.text.endswith('.html'):
                            parsed = urlparse(url.text)
                            filename = os.path.basename(parsed.path)
                            if filename and filename != 'index.html':
                                referenced_files.add(filename)
                                
        except Exception as e:
            self.errors.append(f"Erro ao processar sitemap.xml: {e}")
            
        return referenced_files
    
    def scan_html_files(self):
        """
        Escaneia a pasta em busca de arquivos HTML
        """
        try:
            for file_path in self.folder_path.glob('*.html'):
                if file_path.name != 'index.html':
                    self.html_files.append(file_path)
        except Exception as e:
            self.errors.append(f"Erro ao escanear pasta: {e}")
    
    def create_rename_map(self):
        """
        Cria mapeamento de arquivos para renomeação
        """
        # Obtém arquivos referenciados nos links
        referenced_from_index = self.extract_links_from_index()
        referenced_from_sitemap = self.extract_links_from_sitemap()
        all_referenced = referenced_from_index.union(referenced_from_sitemap)
        
        print(f"Arquivos referenciados encontrados: {len(all_referenced)}")
        for ref in sorted(all_referenced):
            print(f"  - {ref}")
        
        # Escaneia arquivos físicos
        self.scan_html_files()
        print(f"\nArquivos HTML físicos encontrados: {len(self.html_files)}")
        
        # Cria mapeamento baseado em arquivos referenciados
        for referenced_file in all_referenced:
            # Procura arquivo físico correspondente
            original_path = self.folder_path / referenced_file
            
            if original_path.exists():
                cleaned_name = self.clean_filename(referenced_file)
                new_path = self.folder_path / cleaned_name
                
                if referenced_file != cleaned_name:
                    self.rename_map[str(original_path)] = {
                        'old_name': referenced_file,
                        'new_name': cleaned_name,
                        'old_path': original_path,
                        'new_path': new_path,
                        'referenced': True
                    }
        
        # Adiciona arquivos físicos não referenciados mas que precisam de limpeza
        for file_path in self.html_files:
            current_name = file_path.name
            cleaned_name = self.clean_filename(current_name)
            
            if current_name != cleaned_name and str(file_path) not in self.rename_map:
                new_path = self.folder_path / cleaned_name
                self.rename_map[str(file_path)] = {
                    'old_name': current_name,
                    'new_name': cleaned_name,
                    'old_path': file_path,
                    'new_path': new_path,
                    'referenced': False
                }
    
    def check_conflicts(self):
        """
        Verifica conflitos de nomeação
        
        Returns:
            list: Lista de conflitos encontrados
        """
        conflicts = []
        new_names = {}
        
        for old_path, rename_info in self.rename_map.items():
            new_name = rename_info['new_name']
            
            if new_name in new_names:
                conflicts.append({
                    'new_name': new_name,
                    'conflicting_files': [new_names[new_name], rename_info['old_name']]
                })
            else:
                new_names[new_name] = rename_info['old_name']
                
        return conflicts
    
    def resolve_conflicts(self, conflicts):
        """
        Resolve conflitos de nomeação adicionando sufixos numéricos
        
        Args:
            conflicts (list): Lista de conflitos
        """
        for conflict in conflicts:
            new_name = conflict['new_name']
            conflicting_files = conflict['conflicting_files']
            
            name, ext = os.path.splitext(new_name)
            
            for i, old_filename in enumerate(conflicting_files[1:], 2):
                # Encontra o mapeamento correspondente
                for old_path, rename_info in self.rename_map.items():
                    if rename_info['old_name'] == old_filename:
                        resolved_name = f"{name}-{i}{ext}"
                        rename_info['new_name'] = resolved_name
                        rename_info['new_path'] = self.folder_path / resolved_name
                        print(f"Conflito resolvido: {old_filename} -> {resolved_name}")
                        break
    
    def perform_renames(self, backup=True):
        """
        Executa as renomeações de arquivos
        
        Args:
            backup (bool): Se deve criar backup dos arquivos
        """
        if not self.rename_map:
            print("Nenhum arquivo precisa ser renomeado.")
            return
        
        # Cria pasta de backup se solicitado
        backup_folder = None
        if backup:
            backup_folder = self.folder_path / 'backup_arquivos_originais'
            backup_folder.mkdir(exist_ok=True)
            print(f"Pasta de backup criada: {backup_folder}")
        
        successful_renames = []
        
        for old_path, rename_info in self.rename_map.items():
            try:
                old_file = rename_info['old_path']
                new_file = rename_info['new_path']
                
                # Verifica se arquivo de origem existe
                if not old_file.exists():
                    self.errors.append(f"Arquivo não encontrado: {old_file}")
                    continue
                
                # Verifica se arquivo de destino já existe
                if new_file.exists() and new_file != old_file:
                    self.errors.append(f"Arquivo de destino já existe: {new_file}")
                    continue
                
                # Cria backup se solicitado
                if backup and backup_folder:
                    backup_file = backup_folder / old_file.name
                    shutil.copy2(old_file, backup_file)
                    print(f"Backup criado: {backup_file}")
                
                # Renomeia arquivo
                old_file.rename(new_file)
                successful_renames.append({
                    'old': rename_info['old_name'],
                    'new': rename_info['new_name'],
                    'referenced': rename_info['referenced']
                })
                
                print(f"Renomeado: {rename_info['old_name']} -> {rename_info['new_name']}")
                
            except Exception as e:
                error_msg = f"Erro ao renomear {rename_info['old_name']}: {e}"
                self.errors.append(error_msg)
                print(error_msg)
        
        return successful_renames
    
    def update_references(self, successful_renames):
        """
        Atualiza referências nos arquivos após renomeação
        
        Args:
            successful_renames (list): Lista de renomeações bem-sucedidas
        """
        print("\nAtualizando referências nos arquivos...")
        
        # Atualiza index.html
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for rename in successful_renames:
                    old_name = rename['old']
                    new_name = rename['new']
                    
                    # Substitui todas as ocorrências do nome antigo
                    content = content.replace(f'href="{old_name}"', f'href="{new_name}"')
                    content = content.replace(f"href='{old_name}'", f"href='{new_name}'")
                    
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print("Referências atualizadas no index.html")
                
            except Exception as e:
                self.errors.append(f"Erro ao atualizar index.html: {e}")
        
        # Atualiza sitemap.xml
        if self.sitemap_file.exists():
            try:
                tree = ET.parse(self.sitemap_file)
                root = tree.getroot()
                
                # Define namespace se existir
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                updated = False
                
                # Atualiza com namespace
                for url in root.findall('.//ns:loc', namespace):
                    if url.text:
                        for rename in successful_renames:
                            old_name = rename['old']
                            new_name = rename['new']
                            if old_name in url.text:
                                url.text = url.text.replace(old_name, new_name)
                                updated = True
                
                # Se não encontrou com namespace, tenta sem
                if not updated:
                    for url in root.findall('.//loc'):
                        if url.text:
                            for rename in successful_renames:
                                old_name = rename['old']
                                new_name = rename['new']
                                if old_name in url.text:
                                    url.text = url.text.replace(old_name, new_name)
                                    updated = True
                
                if updated:
                    tree.write(self.sitemap_file, encoding='utf-8', xml_declaration=True)
                    print("Referências atualizadas no sitemap.xml")
                    
            except Exception as e:
                self.errors.append(f"Erro ao atualizar sitemap.xml: {e}")
    
    def generate_report(self):
        """
        Gera relatório das operações realizadas
        """
        print("\n" + "="*80)
        print("RELATÓRIO DE RENOMEAÇÃO DE ARQUIVOS")
        print("="*80)
        
        print(f"Total de arquivos a renomear: {len(self.rename_map)}")
        
        if self.rename_map:
            print("\nARQUIVOS QUE SERÃO RENOMEADOS:")
            print("-" * 50)
            
            for i, (old_path, rename_info) in enumerate(self.rename_map.items(), 1):
                ref_status = "Referenciado" if rename_info['referenced'] else "Não referenciado"
                print(f"{i}. {rename_info['old_name']} -> {rename_info['new_name']} ({ref_status})")
        
        if self.errors:
            print(f"\nERROS ENCONTRADOS ({len(self.errors)}):")
            print("-" * 30)
            for error in self.errors:
                print(f"  - {error}")
    
    def run(self):
        """
        Executa o processo completo de renomeação
        """
        print("Iniciando processo de renomeação de arquivos HTML...")
        
        # Cria mapeamento de renomeação
        self.create_rename_map()
        
        # Verifica conflitos
        conflicts = self.check_conflicts()
        if conflicts:
            print(f"\nEncontrados {len(conflicts)} conflitos de nomeação. Resolvendo...")
            self.resolve_conflicts(conflicts)
        
        # Gera relatório
        self.generate_report()
        
        if not self.rename_map:
            print("Todos os arquivos já possuem nomes limpos!")
            return
        
        # Pergunta se deve prosseguir
        proceed = input(f"\nDeseja prosseguir com a renomeação de {len(self.rename_map)} arquivos? (s/n): ").lower()
        if proceed not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return
        
        # Pergunta sobre backup
        backup_choice = input("Criar backup dos arquivos originais? (s/n): ").lower()
        create_backup = backup_choice in ['s', 'sim', 'y', 'yes']
        
        # Executa renomeações
        successful_renames = self.perform_renames(backup=create_backup)
        
        # Atualiza referências se houve renomeações bem-sucedidas
        if successful_renames:
            update_refs = input("\nDeseja atualizar referências no index.html e sitemap.xml? (s/n): ").lower()
            if update_refs in ['s', 'sim', 'y', 'yes']:
                self.update_references(successful_renames)
        
        print(f"\nProcesso concluído!")
        if successful_renames:
            print(f"Arquivos renomeados com sucesso: {len(successful_renames)}")
        if self.errors:
            print(f"Erros encontrados: {len(self.errors)}")


def main():
    """
    Função principal
    """
    print("Script para Renomeação de Arquivos HTML")
    print("=" * 40)
    
    # Configura caminho da pasta
    pasta_atual = input("Digite o caminho da pasta (Enter para pasta atual): ").strip()
    if not pasta_atual:
        pasta_atual = os.getcwd()
    
    if not os.path.exists(pasta_atual):
        print(f"Erro: Pasta '{pasta_atual}' não encontrada!")
        return
    
    # Inicializa e executa o renomeador
    renamer = FileRenamer(pasta_atual)
    renamer.run()


if __name__ == "__main__":
    main()
