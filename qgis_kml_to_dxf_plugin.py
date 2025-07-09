            
# -*- coding: utf-8 -*-
"""
Plugin QGIS para converter KML para DXF preservando texto
"""

import os
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog, QMessageBox, QProgressBar
from qgis.core import QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsWkbTypes, QgsFeature, QgsGeometry, QgsFields, QgsField, QgsPointXY, QgsLayerTreeLayer
from qgis.utils import iface
import processing

class KMLToDXFDialog(QDialog):
    def __init__(self, parent=None):
        super(KMLToDXFDialog, self).__init__(parent)
        self.setWindowTitle("Converter KML para DXF")
        self.setModal(True)
        self.resize(400, 200)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Seleção da camada
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Camada KML:"))
        self.layer_combo = QComboBox()
        self.populate_layer_combo()
        layer_layout.addWidget(self.layer_combo)
        layout.addLayout(layer_layout)
        
        # Seleção da coluna de texto
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Coluna de Texto:"))
        self.text_combo = QComboBox()
        text_layout.addWidget(self.text_combo)
        layout.addLayout(text_layout)
        
        # Botão para atualizar campos
        self.update_fields_btn = QPushButton("Atualizar Campos")
        self.update_fields_btn.clicked.connect(self.update_text_fields)
        layout.addWidget(self.update_fields_btn)
        
        # Seleção do arquivo de saída
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Arquivo DXF:"))
        self.output_line = QLabel("Selecione o arquivo...")
        self.output_line.setStyleSheet("border: 1px solid gray; padding: 5px;")
        output_layout.addWidget(self.output_line)
        self.browse_btn = QPushButton("Procurar")
        self.browse_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.browse_btn)
        layout.addLayout(output_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Botões
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton("Converter")
        self.convert_btn.clicked.connect(self.convert_kml_to_dxf)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Conectar sinal de mudança de camada
        self.layer_combo.currentTextChanged.connect(self.update_text_fields)
        
        # Variável para armazenar o arquivo de saída
        self.output_file = None
        
    def populate_layer_combo(self):
        """Popula o combo box com as camadas vetoriais do projeto"""
        self.layer_combo.clear()
        project = QgsProject.instance()
        
        # Método 1: Usar mapLayers() - mais seguro
        for layer_id, layer in project.mapLayers().items():
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer_id)
                
        # Método 2: Se você precisar usar layerTreeRoot, faça assim:
        # root = project.layerTreeRoot()
        # for child in root.children():
        #     if isinstance(child, QgsLayerTreeLayer):
        #         layer = child.layer()
        #         if isinstance(layer, QgsVectorLayer):
        #             self.layer_combo.addItem(layer.name(), layer.id())
                
    def get_vector_layers_from_tree(self, group):
        """Recursivamente obtém todas as camadas vetoriais da árvore de camadas"""
        layers = []
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if isinstance(layer, QgsVectorLayer):
                    layers.append(layer)
            elif hasattr(child, 'children'):  # É um grupo
                layers.extend(self.get_vector_layers_from_tree(child))
        return layers
                
    def update_text_fields(self):
        """Atualiza os campos de texto disponíveis baseado na camada selecionada"""
        self.text_combo.clear()
        
        if self.layer_combo.currentData():
            layer_id = self.layer_combo.currentData()
            layer = QgsProject.instance().mapLayer(layer_id)
            
            if layer:
                fields = layer.fields()
                for field in fields:
                    if field.type() == 10:  # QString
                        self.text_combo.addItem(field.name())
                        
    def browse_output_file(self):
        """Abre diálogo para selecionar arquivo de saída"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar arquivo DXF",
            "",
            "Arquivos DXF (*.dxf)"
        )
        
        if filename:
            self.output_file = filename
            self.output_line.setText(os.path.basename(filename))
            
    def convert_kml_to_dxf(self):
        """Converte a camada KML para DXF"""
        try:
            # Validações
            if not self.layer_combo.currentData():
                QMessageBox.warning(self, "Aviso", "Selecione uma camada!")
                return
                
            if not self.text_combo.currentText():
                QMessageBox.warning(self, "Aviso", "Selecione uma coluna de texto!")
                return
                
            if not self.output_file:
                QMessageBox.warning(self, "Aviso", "Selecione um arquivo de saída!")
                return
                
            # Obter camada selecionada
            layer_id = self.layer_combo.currentData()
            layer = QgsProject.instance().mapLayer(layer_id)
            
            if not layer:
                QMessageBox.critical(self, "Erro", "Camada não encontrada!")
                return
                
            # Obter nome da coluna de texto
            text_field = self.text_combo.currentText()
            
            # Mostrar barra de progresso
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Progresso indeterminado
            
            # Desabilitar botões
            self.convert_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            
            # Processar a conversão
            self.process_conversion(layer, text_field)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro durante a conversão: {str(e)}")
        finally:
            # Restaurar interface
            self.progress_bar.setVisible(False)
            self.convert_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            
    def process_conversion(self, layer, text_field):
        """Processa a conversão da camada"""
        try:
            # Criar camada temporária para pontos com texto
            temp_layer = self.create_point_layer_with_text(layer, text_field)
            
            if not temp_layer:
                QMessageBox.critical(self, "Erro", "Erro ao criar camada temporária!")
                return
                
            # Exportar para DXF
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "DXF"
            options.fileEncoding = "UTF-8"
            
            # Configurações específicas para DXF
            options.datasourceOptions = [
                "HEADER=MINIMAL"  # Cabeçalho mínimo para compatibilidade
            ]
            
            transform_context = QgsProject.instance().transformContext()
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                temp_layer,
                self.output_file,
                transform_context,
                options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                QMessageBox.information(
                    self, 
                    "Sucesso", 
                    f"Arquivo DXF criado com sucesso!\nLocalização: {self.output_file}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Erro", 
                    f"Erro ao criar arquivo DXF: {error[1]}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro no processamento: {str(e)}")
            
    def create_point_layer_with_text(self, source_layer, text_field):
        """Cria uma camada de pontos com o texto como atributo"""
        try:
            # Criar campos para a nova camada
            fields = QgsFields()
            fields.append(QgsField("id", 4))  # Integer
            fields.append(QgsField("text", 10))  # String
            
            # Criar camada temporária
            temp_layer = QgsVectorLayer(
                "Point?crs=" + source_layer.crs().authid(),
                "temp_points",
                "memory"
            )
            
            temp_layer.dataProvider().addAttributes(fields)
            temp_layer.updateFields()
            
            # Processar features
            features_to_add = []
            feature_id = 1
            
            for feature in source_layer.getFeatures():
                geom = feature.geometry()
                text_value = feature[text_field] if text_field in feature.fields().names() else ""
                
                if geom.type() == QgsWkbTypes.PointGeometry:
                    # Se já é ponto, usar diretamente
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(geom)
                    new_feature.setAttributes([feature_id, str(text_value)])
                    features_to_add.append(new_feature)
                    feature_id += 1
                    
                elif geom.type() == QgsWkbTypes.LineGeometry:
                    # Para linhas, usar o centroide
                    centroid = geom.centroid()
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(centroid)
                    new_feature.setAttributes([feature_id, str(text_value)])
                    features_to_add.append(new_feature)
                    feature_id += 1
                    
                elif geom.type() == QgsWkbTypes.PolygonGeometry:
                    # Para polígonos, usar o centroide
                    centroid = geom.centroid()
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(centroid)
                    new_feature.setAttributes([feature_id, str(text_value)])
                    features_to_add.append(new_feature)
                    feature_id += 1
                    
            # Adicionar features à camada
            temp_layer.dataProvider().addFeatures(features_to_add)
            temp_layer.updateExtents()
            
            return temp_layer
            
        except Exception as e:
            print(f"Erro ao criar camada de pontos: {str(e)}")
            return None


class KMLToDXFPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        # Inicializar locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'KMLToDXF_{}.qm'.format(locale)
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            
        # Declarar variáveis de instância
        self.actions = []
        self.menu = self.tr(u'&KML para DXF')
        
    def tr(self, message):
        return QCoreApplication.translate('KMLToDXF', message)
        
    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True, status_tip=None,
                   whats_this=None, parent=None):
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
            
        if whats_this is not None:
            action.setWhatsThis(whats_this)
            
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
            
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
            
        self.actions.append(action)
        return action
        
    def initGui(self):
        """Cria as entradas no menu e toolbar"""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Converter KML para DXF'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        
    def unload(self):
        """Remove as entradas do menu e toolbar"""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&KML para DXF'), action)
            self.iface.removeToolBarIcon(action)
            
    def run(self):
        """Executa o plugin"""
        dialog = KMLToDXFDialog()
        dialog.exec_()


# Função para criar o plugin
def classFactory(iface):
    return KMLToDXFPlugin(iface)
