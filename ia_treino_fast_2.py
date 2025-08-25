# -*- coding: utf-8 -*-
"""
IA Treino FAST - Versão Otimizada
Baseado na versão que está funcionando melhor
"""

import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, BatchNormalization, Dropout
from tensorflow.keras.models import Model

print("🚀 IA TREINO FAST - VERSÃO OTIMIZADA")
print("=" * 50)

# Configurações
images_folder = 'dataset'
masks_folder = 'mascara'
output_folder = 'fast2'

# Criar pasta de resultados se não existir
os.makedirs(output_folder, exist_ok=True)
print(f"📁 Pasta de resultados: {output_folder}")

def load_data_otimizado(limit=None):  # TODAS as imagens do dataset
    """Carrega dados com verificações melhoradas"""
    images = []
    masks = []
    
    all_image_files = sorted(os.listdir(images_folder))
    if limit is None:
        image_files = all_image_files
        print(f"🔍 Carregando TODAS as {len(all_image_files)} imagens do dataset...")
    else:
        image_files = all_image_files[:limit]
        print(f"🔍 Carregando até {limit} imagens...")
    
    for image_file in image_files:
        base_name, ext = os.path.splitext(image_file)
        mask_file = base_name + '_mask' + ext
        
        image_path = os.path.join(images_folder, image_file)
        mask_path = os.path.join(masks_folder, mask_file)
        
        if os.path.exists(image_path) and os.path.exists(mask_path):
            # Carregar imagem
            img = cv2.imread(image_path)
            if img is None:
                continue
                
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (128, 128))  # Manter 128x128 que funciona
            img = img.astype(np.float32) / 255.0
            
            # Carregar máscara
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is None:
                continue
                
            mask = cv2.resize(mask, (128, 128))
            
            # Verificar se máscara tem conteúdo
            if mask.max() > 0:
                mask = (mask > 0).astype(np.float32)  # Usar threshold baixo
                mask = np.expand_dims(mask, axis=-1)
                
                images.append(img)
                masks.append(mask)
                
                mask_pixels = np.sum(mask)
                print(f"   ✓ {image_file}: {mask_pixels:.0f} pixels de estrada")
            else:
                print(f"   ⚠️ {image_file}: Máscara vazia, pulando...")
    
    return np.array(images), np.array(masks)

def unet_fast_otimizado(input_size=(128, 128, 3)):
    """U-Net MELHORADA - Mais camadas e skip connections"""
    inputs = Input(input_size)
    
    # Encoder - MELHORADO com mais camadas
    c1 = Conv2D(64, 3, activation='relu', padding='same')(inputs)
    c1 = Conv2D(64, 3, activation='relu', padding='same')(c1)  # Camada dupla
    c1 = BatchNormalization()(c1)
    p1 = MaxPooling2D((2, 2))(c1)
    
    c2 = Conv2D(128, 3, activation='relu', padding='same')(p1)
    c2 = Conv2D(128, 3, activation='relu', padding='same')(c2)  # Camada dupla
    c2 = BatchNormalization()(c2)
    p2 = MaxPooling2D((2, 2))(c2)
    
    c3 = Conv2D(256, 3, activation='relu', padding='same')(p2)
    c3 = Conv2D(256, 3, activation='relu', padding='same')(c3)  # Camada dupla
    c3 = BatchNormalization()(c3)
    p3 = MaxPooling2D((2, 2))(c3)
    
    # Bottleneck - Mais profundo
    c4 = Conv2D(512, 3, activation='relu', padding='same')(p3)
    c4 = Conv2D(512, 3, activation='relu', padding='same')(c4)
    c4 = BatchNormalization()(c4)
    c4 = Dropout(0.3)(c4)  # Dropout mais forte
    
    # Decoder - MELHORADO com skip connections
    u5 = UpSampling2D((2, 2))(c4)
    u5 = concatenate([u5, c3])
    c5 = Conv2D(256, 3, activation='relu', padding='same')(u5)
    c5 = Conv2D(256, 3, activation='relu', padding='same')(c5)
    c5 = BatchNormalization()(c5)
    
    u6 = UpSampling2D((2, 2))(c5)
    u6 = concatenate([u6, c2])
    c6 = Conv2D(128, 3, activation='relu', padding='same')(u6)
    c6 = Conv2D(128, 3, activation='relu', padding='same')(c6)
    c6 = BatchNormalization()(c6)
    
    u7 = UpSampling2D((2, 2))(c6)
    u7 = concatenate([u7, c1])
    c7 = Conv2D(64, 3, activation='relu', padding='same')(u7)
    c7 = Conv2D(64, 3, activation='relu', padding='same')(c7)
    
    outputs = Conv2D(1, 1, activation='sigmoid')(c7)
    
    model = Model(inputs=[inputs], outputs=[outputs])
    return model

# Carregar dados
images, masks = load_data_otimizado()  # TODAS as imagens do dataset

if len(images) == 0:
    print("❌ Nenhuma imagem carregada! Verifique os dados.")
    exit()

print(f"📊 Total de imagens carregadas: {len(images)}")

# Criar modelo
print("🔧 Criando modelo U-Net Fast Otimizado...")
model = unet_fast_otimizado()

# Compilar com configurações MELHORADAS
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),  # Learning rate menor
    loss='binary_crossentropy',
    metrics=['accuracy', 'precision', 'recall']  # Mais métricas
)

print("🎯 Iniciando treinamento otimizado...")

# Treinar (usar validação com dataset completo)
if len(images) >= 8:
    # Dividir em treino/validação
    train_images, val_images, train_masks, val_masks = train_test_split(
        images, masks, test_size=0.15, random_state=42  # 15% para validação
    )
    
    print(f"📊 Dataset completo dividido:")
    print(f"   • Treino: {len(train_images)} imagens")
    print(f"   • Validação: {len(val_images)} imagens")
    
    history = model.fit(
        train_images, train_masks,
        epochs=35,  # MAIS epochs para aprender melhor
        validation_data=(val_images, val_masks),
        verbose=1,
        batch_size=1  # Batch menor para melhor aprendizado
    )
    test_image = val_images[0]
    test_mask_real = val_masks[0]

print("✅ Treinamento concluído!")

# 💾 SALVAR O MODELO TREINADO
model_path = os.path.join(output_folder, 'modelo_fast2.h5')
model.save(model_path)
print(f"🎯 Modelo salvo em: {model_path}")

# Fazer previsão EM TODAS AS IMAGENS DE VALIDAÇÃO
print("🔮 Fazendo previsões em TODAS as imagens de validação...")
print(f"📊 Total de imagens para processar: {len(val_images)}")

# Processar todas as imagens de validação
all_predictions = []
for i, val_img in enumerate(val_images):
    test_image_input = np.expand_dims(val_img, axis=0)
    predicted_mask = model.predict(test_image_input, verbose=0)
    all_predictions.append(predicted_mask[0])
    print(f"   ✓ Processada imagem {i+1}/{len(val_images)}")

print(f"📊 Estatísticas das previsões:")
for i, pred in enumerate(all_predictions):
    print(f"   • Imagem {i+1}: Min={pred.min():.4f}, Max={pred.max():.4f}, Média={pred.mean():.4f}")

# Testar thresholds OTIMIZADOS
thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
print(f"\n🎚️ Testando thresholds na primeira imagem:")

# Usar primeira imagem para encontrar melhor threshold
predicted_mask = all_predictions[0]

resultados_threshold = {}
for thresh in thresholds:
    mask_test = (predicted_mask > thresh).astype(np.uint8)
    white_pixels = np.sum(mask_test)
    percentage = (white_pixels / (128*128)) * 100
    
    resultados_threshold[thresh] = {
        'pixels': white_pixels,
        'percentage': percentage,
        'mask': mask_test
    }
    
    print(f"   • Threshold {thresh}: {white_pixels} pixels ({percentage:.1f}%)")

# Escolher melhor threshold (baseado em ter detecção mas não demais)
best_threshold = 0.3
best_score = 0

for thresh, dados in resultados_threshold.items():
    percentage = dados['percentage']
    # Score baseado em ter entre 1% e 25% da imagem detectada
    if 1 <= percentage <= 25:
        score = 100 - abs(percentage - 8)  # Ideal em torno de 8%
        if score > best_score:
            best_score = score
            best_threshold = thresh

print(f"\n🏆 Melhor threshold escolhido: {best_threshold}")
print(f"   • Detecção: {resultados_threshold[best_threshold]['percentage']:.1f}%")

# 🖼️ CRIAR COMPARAÇÕES LADO A LADO DE TODAS AS IMAGENS
print(f"\n🖼️ Criando comparações lado a lado de TODAS as {len(val_images)} imagens...")

# Criar pasta específica para comparações
comparacoes_folder = os.path.join(output_folder, 'comparacoes_todas')
os.makedirs(comparacoes_folder, exist_ok=True)

# Processar cada imagem de validação
for i in range(len(val_images)):
    val_img = val_images[i]
    val_mask_real = val_masks[i]
    predicted_mask_img = all_predictions[i]
    
    # Aplicar melhor threshold
    best_mask = (predicted_mask_img > best_threshold).astype(np.uint8)
    
    # Converter para BGR para salvar
    original_bgr = cv2.cvtColor(val_img, cv2.COLOR_RGB2BGR)
    original_display = (original_bgr * 255).astype(np.uint8)
    
    # Converter máscaras para 3 canais
    mask_real_3ch = cv2.cvtColor((val_mask_real.squeeze() * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    mask_pred_3ch = cv2.cvtColor((best_mask.squeeze() * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    
    # Criar comparação lado a lado: Original | Real | Prevista
    comparison = np.hstack((original_display, mask_real_3ch, mask_pred_3ch))
    
    # Salvar comparação individual
    comparison_path = os.path.join(comparacoes_folder, f'comparacao_{i+1:02d}.png')
    cv2.imwrite(comparison_path, comparison)
    
    # Salvar também as imagens individuais
    individual_folder = os.path.join(comparacoes_folder, f'imagem_{i+1:02d}')
    os.makedirs(individual_folder, exist_ok=True)
    
    cv2.imwrite(os.path.join(individual_folder, 'original.png'), original_display)
    cv2.imwrite(os.path.join(individual_folder, 'mascara_real.png'), mask_real_3ch)
    cv2.imwrite(os.path.join(individual_folder, 'mascara_prevista.png'), mask_pred_3ch)
    
    print(f"   ✓ Comparação {i+1}/{len(val_images)} salva")

# Criar uma imagem GRID com todas as comparações
print("� Criando GRID com todas as comparações...")

# Calcular dimensões do grid
num_images = len(val_images)
cols = min(4, num_images)  # Máximo 4 colunas
rows = (num_images + cols - 1) // cols  # Arredondar para cima

# Criar grid grande
grid_height = rows * 128 * 3  # Cada linha tem altura 128, 3 por causa do lado a lado
grid_width = cols * (128 * 3)  # Cada coluna tem largura 128*3 (original+real+prevista)
grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)

for i in range(num_images):
    row = i // cols
    col = i % cols
    
    val_img = val_images[i]
    val_mask_real = val_masks[i]
    predicted_mask_img = all_predictions[i]
    best_mask = (predicted_mask_img > best_threshold).astype(np.uint8)
    
    # Preparar imagens pequenas para o grid
    original_small = cv2.resize((cv2.cvtColor(val_img, cv2.COLOR_RGB2BGR) * 255).astype(np.uint8), (128, 128))
    real_small = cv2.resize((val_mask_real.squeeze() * 255).astype(np.uint8), (128, 128))
    pred_small = cv2.resize((best_mask.squeeze() * 255).astype(np.uint8), (128, 128))
    
    # Converter para 3 canais
    real_small_3ch = cv2.cvtColor(real_small, cv2.COLOR_GRAY2BGR)
    pred_small_3ch = cv2.cvtColor(pred_small, cv2.COLOR_GRAY2BGR)
    
    # Posição no grid
    y_start = row * 128
    y_end = y_start + 128
    x_start = col * (128 * 3)
    
    # Colocar as 3 imagens lado a lado
    grid[y_start:y_end, x_start:x_start+128] = original_small
    grid[y_start:y_end, x_start+128:x_start+256] = real_small_3ch
    grid[y_start:y_end, x_start+256:x_start+384] = pred_small_3ch

# Salvar grid completo
grid_path = os.path.join(output_folder, 'grid_todas_comparacoes.png')
cv2.imwrite(grid_path, grid)

print(f"🎉 TODAS as comparações criadas!")
print(f"   📁 Pasta individual: {comparacoes_folder}/")
print(f"   🖼️ Grid completo: {grid_path}")

# Salvar resultados (manter código original para primeira imagem)
print(f"\n💾 Salvando resultados principais...")

# Usar primeira imagem para análises principais
test_image = val_images[0]
test_mask_real = val_masks[0]
predicted_mask = all_predictions[0]

# 1. Imagem original (primeira de validação)
original_bgr = cv2.cvtColor(test_image, cv2.COLOR_RGB2BGR)
original_path = os.path.join(output_folder, 'imagem_original.png')
cv2.imwrite(original_path, (original_bgr * 255).astype(np.uint8))

# 2. Máscara prevista (melhor threshold) - primeira imagem
best_mask = (predicted_mask > best_threshold).astype(np.uint8)
mask_to_save = (best_mask.squeeze() * 255).astype(np.uint8)
mask_path = os.path.join(output_folder, f'mascara_prevista_threshold_{best_threshold}.png')
cv2.imwrite(mask_path, mask_to_save)

# 3. Máscara real
real_mask = (test_mask_real.squeeze() * 255).astype(np.uint8)
real_mask_path = os.path.join(output_folder, 'mascara_real.png')
cv2.imwrite(real_mask_path, real_mask)

# 4. Todas as máscaras por threshold (primeira imagem)
for thresh in thresholds:
    thresh_mask_result = (predicted_mask > thresh).astype(np.uint8)
    thresh_mask = (thresh_mask_result.squeeze() * 255).astype(np.uint8)
    thresh_path = os.path.join(output_folder, f'mascara_threshold_{thresh:.2f}.png')
    cv2.imwrite(thresh_path, thresh_mask)

# 5. Comparação visual
try:
    plt.figure(figsize=(20, 8))
    
    # Plot principal: Original, Real, Melhor Prevista
    plt.subplot(2, 4, 1)
    plt.imshow(test_image)
    plt.title('Imagem Original')
    plt.axis('off')
    
    plt.subplot(2, 4, 2)
    plt.imshow(test_mask_real.squeeze(), cmap='gray')
    plt.title('Máscara Real')
    plt.axis('off')
    
    plt.subplot(2, 4, 3)
    plt.imshow(best_mask.squeeze(), cmap='gray')
    plt.title(f'Melhor Prevista\n(Threshold {best_threshold})')
    plt.axis('off')
    
    # Comparação lado a lado
    mask_3ch = cv2.cvtColor(mask_to_save, cv2.COLOR_GRAY2BGR)
    real_mask_3ch = cv2.cvtColor(real_mask, cv2.COLOR_GRAY2BGR)
    original_display = (original_bgr * 255).astype(np.uint8)
    comparison = np.hstack((original_display, real_mask_3ch, mask_3ch))
    
    plt.subplot(2, 4, 4)
    plt.imshow(cv2.cvtColor(comparison, cv2.COLOR_BGR2RGB))
    plt.title('Original | Real | Prevista')
    plt.axis('off')
    
    # Mostrar diferentes thresholds
    for i, thresh in enumerate([0.1, 0.2, 0.3, 0.4]):
        if thresh in thresholds:  # Verificar se threshold existe
            plt.subplot(2, 4, 5 + i)
            thresh_mask_plot = (predicted_mask > thresh).astype(np.uint8)
            plt.imshow(thresh_mask_plot.squeeze(), cmap='gray')
            white_pixels = np.sum(thresh_mask_plot)
            percentage = (white_pixels / (128*128)) * 100
            plt.title(f'Threshold {thresh}\n{percentage:.1f}%')
            plt.axis('off')
    
    plt.tight_layout()
    plot_path = os.path.join(output_folder, 'analise_completa.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Análise visual salva em: {plot_path}")
    
except Exception as e:
    print(f"⚠️ Erro ao criar visualização: {e}")

# Salvar comparação lado a lado
comparison_path = os.path.join(output_folder, 'comparacao_lado_a_lado.png')
cv2.imwrite(comparison_path, comparison)

print(f"\n🎉 RESULTADOS FINAIS:")
print(f"   📁 Pasta: {output_folder}/")
print(f"   🎯 Melhor threshold: {best_threshold}")
best_percentage = (np.sum((predicted_mask > best_threshold).astype(np.uint8)) / (128*128)) * 100
print(f"   📊 Detecção: {best_percentage:.1f}%")
print(f"   🖼️ Principais arquivos:")
print(f"      • {mask_path}")
print(f"      • {comparison_path}")
print(f"      • analise_completa.png")
print(f"      • {model_path} (MODELO TREINADO)")
print(f"   🔥 NOVIDADES:")
print(f"      • {grid_path} (GRID COM TODAS)")
print(f"      • {comparacoes_folder}/ (COMPARAÇÕES INDIVIDUAIS)")
print(f"      • Total de {len(val_images)} imagens processadas!")

print(f"\n💡 Para usar este threshold no script principal:")
print(f"   predicted_mask_binary = (predicted_mask > {best_threshold}).astype(np.uint8)")

print(f"\n🚀 Para carregar o modelo salvo:")
print(f"   from tensorflow.keras.models import load_model")
print(f"   model = load_model('{model_path}')")
