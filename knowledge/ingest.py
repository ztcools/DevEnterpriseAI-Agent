# -*- coding: utf-8 -*-
"""
知识库入库脚本模块

提供文档加载、分块、向量化存储的完整流程。
支持多种文档格式（txt、pdf、docx、markdown等）。
"""

import os
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import get_settings
from utils import get_logger


class DocumentLoader:
    """文档加载器

    支持多种格式文档的加载。
    """

    LOADERS = {
        ".txt": TextLoader,
        ".pdf": PyPDFLoader,
        ".docx": UnstructuredWordDocumentLoader,
        ".md": UnstructuredMarkdownLoader,
    }

    def __init__(self, encoding: str = "utf-8"):
        """初始化文档加载器

        Args:
            encoding: 文件编码，默认utf-8
        """
        self.encoding = encoding
        self.logger = get_logger(self.__class__.__name__)

    def load(self, file_path: str) -> List[Document]:
        """加载单个文档

        Args:
            file_path: 文件路径

        Returns:
            List[Document]: 文档列表
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in self.LOADERS:
            raise ValueError(f"Unsupported file format: {suffix}")

        loader_class = self.LOADERS[suffix]
        try:
            if suffix == ".txt":
                loader = loader_class(file_path, encoding=self.encoding)
            else:
                loader = loader_class(file_path)

            documents = loader.load()
            self.logger.info(f"Loaded document: {file_path}, pages: {len(documents)}")
            return documents
        except Exception as e:
            self.logger.error(f"Failed to load document {file_path}: {e}")
            raise

    def load_directory(
        self,
        directory: str,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[Document]:
        """加载目录下所有文档

        Args:
            directory: 目录路径
            recursive: 是否递归搜索子目录
            file_types: 指定文件扩展名列表，如 [".txt", ".pdf"]

        Returns:
            List[Document]: 文档列表
        """
        if file_types is None:
            file_types = list(self.LOADERS.keys())

        path = Path(directory)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        documents = []
        pattern = "**/*" if recursive else "*"

        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                try:
                    docs = self.load(str(file_path))
                    documents.extend(docs)
                except Exception as e:
                    self.logger.warning(f"Skipping {file_path}: {e}")
                    continue

        self.logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents


class KnowledgeIngestor:
    """知识库入库器

    负责文档的分块、向量化、存储。
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """初始化知识库入库器

        Args:
            persist_directory: 向量库持久化目录
            embedding_model: 嵌入模型名称
            chunk_size: 分块大小
            chunk_overlap: 分块重叠大小
            api_key: API密钥
            base_url: API地址
        """
        settings = get_settings()

        self.persist_directory = persist_directory or settings.vectorstore.persist_directory
        self.embedding_model = embedding_model or settings.vectorstore.embedding_model
        self.chunk_size = chunk_size or settings.vectorstore.chunk_size
        self.chunk_overlap = chunk_overlap or settings.vectorstore.chunk_overlap

        self.api_key = api_key or settings.llm.api_key
        self.base_url = base_url or settings.llm.base_url

        self.logger = get_logger(self.__class__.__name__)

        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[Chroma] = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """获取嵌入模型实例

        Returns:
            OpenAIEmbeddings: 嵌入模型实例
        """
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.embedding_model,
            )
        return self._embeddings

    def _get_vectorstore(self) -> Chroma:
        """获取向量库实例

        Returns:
            Chroma: 向量库实例
        """
        if self._vectorstore is None:
            embeddings = self._get_embeddings()
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=embeddings,
            )
        return self._vectorstore

    def ingest_documents(
        self,
        documents: List[Document],
        metadata: Optional[Dict[str, Any]] = None,
        batch_size: int = 100,
    ) -> int:
        """入库文档

        Args:
            documents: 文档列表
            metadata: 公共元数据
            batch_size: 批次大小

        Returns:
            int: 入库文档块数
        """
        if not documents:
            return 0

        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            if metadata:
                doc.metadata.update(metadata)

            doc.metadata["file_hash"] = hashlib.md5(
                doc.page_content.encode("utf-8")
            ).hexdigest()

        chunks = self._text_splitter.split_documents(documents)
        self.logger.info(f"Split into {len(chunks)} chunks")

        vectorstore = self._get_vectorstore()

        total_chunks = len(chunks)
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            vectorstore.add_documents(batch)
            self.logger.info(f"Ingested batch {i//batch_size + 1}, progress: {min(i+batch_size, total_chunks)}/{total_chunks}")

        self.logger.info(f"Successfully ingested {total_chunks} chunks")
        return total_chunks

    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """入库单个文件

        Args:
            file_path: 文件路径
            metadata: 元数据

        Returns:
            int: 入库文档块数
        """
        loader = DocumentLoader()
        documents = loader.load(file_path)

        file_metadata = metadata or {}
        file_metadata["source"] = str(file_path)

        return self.ingest_documents(documents, file_metadata)

    def ingest_directory(
        self,
        directory: str,
        recursive: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        file_types: Optional[List[str]] = None,
    ) -> int:
        """入库目录下的所有文件

        Args:
            directory: 目录路径
            recursive: 是否递归
            metadata: 公共元数据
            file_types: 文件类型列表

        Returns:
            int: 入库文档块数
        """
        loader = DocumentLoader()
        documents = loader.load_directory(directory, recursive, file_types)

        return self.ingest_documents(documents, metadata)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """相似度搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter: 元数据过滤条件

        Returns:
            List[Document]: 相似文档列表
        """
        vectorstore = self._get_vectorstore()
        return vectorstore.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        """带相似度分数的搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter: 元数据过滤条件

        Returns:
            List[tuple]: (文档, 分数)列表
        """
        vectorstore = self._get_vectorstore()
        return vectorstore.similarity_search_with_score(query, k=k, filter=filter)

    def delete(self, filter: Dict[str, Any]) -> None:
        """删除向量

        Args:
            filter: 删除条件
        """
        vectorstore = self._get_vectorstore()
        vectorstore.delete(filter)

    def clear(self) -> None:
        """清空向量库"""
        vectorstore = self._get_vectorstore()
        vectorstore.delete(filter={})
        self.logger.info("Vector store cleared")

    def persist(self) -> None:
        """持久化向量库"""
        if self._vectorstore is not None:
            self._vectorstore.persist()
            self.logger.info("Vector store persisted")


def create_ingestor(**kwargs) -> KnowledgeIngestor:
    """创建知识库入库器工厂函数

    Args:
        **kwargs: 入库器初始化参数

    Returns:
        KnowledgeIngestor: 入库器实例
    """
    return KnowledgeIngestor(**kwargs)
