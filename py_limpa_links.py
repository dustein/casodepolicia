#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para análise e limpeza de links em arquivos HTML e sitemap.xml
Remove acentuações e caracteres especiais dos URLs para otimizar indexação
"""

import os
import re
import unicodedata
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


class LinkCleaner:
    def __init__(self, folder_path):
        """
        Inicializa o limpador de links
        
        Args:
            folder_path (str): Caminho para a pasta contendo os arquivos
        """
        self.folder_path = folder_path
        self.index_file = os.path.join(folder_path, 'index.html')
        self.sitemap_file = os.path.join(folder_path, 'sitemap.xml')
        self.html_files = []
        self.links_found = []
        self.cleaned_links = []
        
    def remove_accents(self, text):
        """
        Remove acentos e normaliza texto para ASCII
        
        Args:
            text (str): Texto a ser normalizado
            
        Returns:
            str: Texto sem acentos
        """
        # Normalização NFD - decompõe caracteres acentuados
        nfd = unicodedata.normalize('NFD', text)
        # Remove caracteres de combinação (acentos)
        ascii_text = ''.join(c for c in nfd if unicodedata.combining(c) == 0)
        return ascii_text
    
    def clean_special_characters(self, text):
        """
        Remove ou substitui caracteres especiais problemáticos para URLs
        
        Args:
            text (str): Texto a ser limpo
            
        Returns:
            str: Texto limpo
        """
        # Substitui espaços por hífens
        text = re.sub(r'\s+', '-', text)
        # Remove caracteres especiais, mantendo apenas alfanuméricos, hífens e pontos
        text = re.sub(r'[^a-zA-Z0-9\-\._/]', '', text)
        # Remove múltiplos hífens consecutivos
        text = re.sub(r'-+', '-', text)
        # Remove hífens no início e fim
        text = text.strip('-')
        return text
    
    def clean_url(self, url):
        """
        Limpa completamente uma URL
        
        Args:
            url (str): URL a ser limpa
            
        Returns:
            str: URL limpa
        """
        # Decodifica URL se estiver codificada
        url = unquote(url)
        # Remove acentos
        url = self.remove_accents(url)
        # Limpa caracteres especiais
        url = self.clean_special_characters(url)
        # Converte para minúsculas
        url = url.lower()
        return url
    
    def extract_links_from_html(self, html_file):
        """
        Extrai links de um arquivo HTML
        
        Args:
            html_file (str): Caminho para o arquivo HTML
            
        Returns:
            list: Lista de links encontrados
        """
        links = []
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            soup = BeautifulSoup(content, 'html.parser')
            
            # Encontra todos os links <a href="">
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and href.endswith('.html'):
                    links.append({
                        'original': href,
                        'file': html_file,
                        'type': 'html_link'
                    })
                    
        except Exception as e:
            print(f"Erro ao processar {html_file}: {e}")
            
        return links
    
    def extract_links_from_sitemap(self, sitemap_file):
        """
        Extrai links do sitemap.xml
        
        Args:
            sitemap_file (str): Caminho para o arquivo sitemap.xml
            
        Returns:
            list: Lista de links encontrados
        """
        links = []
        try:
            tree = ET.parse(sitemap_file)
            root = tree.getroot()
            
            # Define namespace se existir
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Tenta diferentes formatos de sitemap
            # Sitemap padrão com <url><loc>
            for url in root.findall('.//ns:loc', namespace):
                if url.text and url.text.endswith('.html'):
                    links.append({
                        'original': url.text,
                        'file': sitemap_file,
                        'type': 'sitemap_url'
                    })
            
            # Se não encontrou com namespace, tenta sem
            if not links:
                for url in root.findall('.//loc'):
                    if url.text and url.text.endswith('.html'):
                        links.append({
                            'original': url.text,
                            'file': sitemap_file,
                            'type': 'sitemap_url'
                        })
                        
        except Exception as e:
            print(f"Erro ao processar sitemap {sitemap_file}: {e}")
            
        return links
    
    def scan_folder(self):
        """
        Escaneia a pasta em busca de arquivos HTML
        """
        for file in os.listdir(self.folder_path):
            if file.endswith('.html'):
                self.html_files.append(os.path.join(self.folder_path, file))
    
    def process_all_links(self):
        """
        Processa todos os links encontrados nos arquivos
        """
        print("Iniciando análise de links...")
        
        # Escaneia pasta
        self.scan_folder()
        
        # Processa index.html se existir
        if os.path.exists(self.index_file):
            print(f"Processando {self.index_file}...")
            index_links = self.extract_links_from_html(self.index_file)
            self.links_found.extend(index_links)
        
        # Processa sitemap.xml se existir
        if os.path.exists(self.sitemap_file):
            print(f"Processando {self.sitemap_file}...")
            sitemap_links = self.extract_links_from_sitemap(self.sitemap_file)
            self.links_found.extend(sitemap_links)
        
        # Processa outros arquivos HTML na pasta
        for html_file in self.html_files:
            if html_file != self.index_file:
                print(f"Processando {html_file}...")
                other_links = self.extract_links_from_html(html_file)
                self.links_found.extend(other_links)
        
        # Limpa todos os links
        for link_data in self.links_found:
            original_url = link_data['original']
            cleaned_url = self.clean_url(original_url)
            
            self.cleaned_links.append({
                'original': original_url,
                'cleaned': cleaned_url,
                'file': link_data['file'],
                'type': link_data['type'],
                'needs_update': original_url != cleaned_url
            })
    
    def generate_report(self):
        """
        Gera relatório dos links processados
        """
        print("\n" + "="*80)
        print("RELATÓRIO DE ANÁLISE DE LINKS")
        print("="*80)
        
        total_links = len(self.cleaned_links)
        needs_update = sum(1 for link in self.cleaned_links if link['needs_update'])
        
        print(f"Total de links analisados: {total_links}")
        print(f"Links que precisam de atualização: {needs_update}")
        print(f"Links já otimizados: {total_links - needs_update}")
        
        if needs_update > 0:
            print("\nLINKS QUE PRECISAM SER ATUALIZADOS:")
            print("-" * 50)
            
            for i, link in enumerate(self.cleaned_links, 1):
                if link['needs_update']:
                    print(f"{i}. Arquivo: {os.path.basename(link['file'])}")
                    print(f"   Tipo: {link['type']}")
                    print(f"   Original: {link['original']}")
                    print(f"   Limpo: {link['cleaned']}")
                    print()
    
    def save_cleaned_urls_file(self, output_file='urls_limpas.txt'):
        """
        Salva lista de URLs limpas em arquivo
        
        Args:
            output_file (str): Nome do arquivo de saída
        """
        output_path = os.path.join(self.folder_path, output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("URLs ORIGINAIS -> URLs LIMPAS\n")
            f.write("=" * 50 + "\n\n")
            
            for link in self.cleaned_links:
                if link['needs_update']:
                    f.write(f"Arquivo: {os.path.basename(link['file'])}\n")
                    f.write(f"Tipo: {link['type']}\n")
                    f.write(f"Original: {link['original']}\n")
                    f.write(f"Limpo: {link['cleaned']}\n")
                    f.write("-" * 30 + "\n")
        
        print(f"Arquivo salvo: {output_path}")
    
    def update_files(self, backup=True):
        """
        Atualiza os arquivos com URLs limpas
        
        Args:
            backup (bool): Se deve criar backup dos arquivos originais
        """
        print("\nATUALIZANDO ARQUIVOS...")
        
        files_to_update = {}
        
        # Agrupa atualizações por arquivo
        for link in self.cleaned_links:
            if link['needs_update']:
                file_path = link['file']
                if file_path not in files_to_update:
                    files_to_update[file_path] = []
                files_to_update[file_path].append(link)
        
        # Atualiza cada arquivo
        for file_path, links in files_to_update.items():
            try:
                # Faz backup se solicitado
                if backup:
                    backup_path = file_path + '.backup'
                    with open(file_path, 'r', encoding='utf-8') as original:
                        with open(backup_path, 'w', encoding='utf-8') as backup_file:
                            backup_file.write(original.read())
                    print(f"Backup criado: {backup_path}")
                
                # Lê conteúdo atual
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Aplica substituições
                for link in links:
                    content = content.replace(link['original'], link['cleaned'])
                
                # Salva arquivo atualizado
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Arquivo atualizado: {file_path}")
                
            except Exception as e:
                print(f"Erro ao atualizar {file_path}: {e}")


def main():
    """
    Função principal
    """
    # Configura caminho da pasta (modifique conforme necessário)
    pasta_atual = input("Digite o caminho da pasta (Enter para pasta atual): ").strip()
    if not pasta_atual:
        pasta_atual = os.getcwd()
    
    if not os.path.exists(pasta_atual):
        print(f"Erro: Pasta '{pasta_atual}' não encontrada!")
        return
    
    # Inicializa o limpador
    cleaner = LinkCleaner(pasta_atual)
    
    # Processa todos os links
    cleaner.process_all_links()
    
    # Gera relatório
    cleaner.generate_report()
    
    # Salva arquivo com URLs limpas
    cleaner.save_cleaned_urls_file()
    
    # Pergunta se deve atualizar os arquivos
    update_choice = input("\nDeseja atualizar os arquivos automaticamente? (s/n): ").lower()
    if update_choice in ['s', 'sim', 'y', 'yes']:
        backup_choice = input("Criar backup dos arquivos originais? (s/n): ").lower()
        create_backup = backup_choice in ['s', 'sim', 'y', 'yes']
        cleaner.update_files(backup=create_backup)
    
    print("\nProcessamento concluído!")


if __name__ == "__main__":
    main()
