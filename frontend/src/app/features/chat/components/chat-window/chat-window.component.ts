import {
  ChangeDetectionStrategy, ChangeDetectorRef, Component, DestroyRef, NgZone,
  inject, input, output, signal, computed, OnInit, ElementRef, viewChild,
} from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { takeUntilDestroyed, toObservable, toSignal } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Conversacion, Mensaje, ChatReadEvent } from '../../models/chat.models';
import { ChatService } from '../../services/chat.service';
import { ChatSocketService } from '../../services/chat-socket.service';
import { MessageInputComponent } from '../message-input/message-input.component';
import { ImageViewerDialogComponent, ImageViewerData } from '../image-viewer-dialog/image-viewer-dialog.component';
import { compressImage, compressedExtension } from '../../utils/image-compressor';
import { ChatMessageEditedEvent } from '../../services/chat-socket.service';
import { MatChipsModule } from '@angular/material/chips';

type UploadStep = 'compressing' | 'uploading' | null;

const MODULE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard financiero',
  proyectos: 'Proyectos',
  terceros: 'Terceros',
  contabilidad: 'Contabilidad',
  general: 'Asistente general',
};

const BOT_SUGGESTIONS: Record<string, string[]> = {
  dashboard: [
    '¿Cuáles son mis ingresos del mes?',
    'Muéstrame el estado de resultados',
    '¿Cómo está el flujo de caja?',
  ],
  proyectos: [
    '¿Qué proyectos están activos?',
    '¿Hay tareas vencidas?',
    'Resumen de avance de proyectos',
  ],
  terceros: [
    '¿Cuántos clientes activos tengo?',
    'Listar proveedores principales',
    '¿Qué terceros se crearon este mes?',
  ],
  contabilidad: [
    '¿Cuál es el saldo de la cuenta 1305?',
    'Muéstrame el balance de prueba',
    'Explícame la retención en la fuente',
  ],
  general: [
    '¿Qué módulos tengo activos?',
    '¿Cómo funciona la sincronización?',
    '¿Cuál es la tarifa del IVA en Colombia?',
  ],
};

@Component({
  selector: 'app-chat-window',
  imports: [
    MatIconModule, MatButtonModule, MatProgressBarModule, MatTooltipModule, MatInputModule,
    MatChipsModule, DatePipe, FormsModule, MessageInputComponent,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(dragover)': 'onDragOver($event)',
    '(dragleave)': 'onDragLeave($event)',
    '(drop)': 'onDrop($event)',
  },
  template: `
    @if (loadingMessages()) {
      <mat-progress-bar mode="indeterminate" />
    }

    @if (isBot()) {
      <div class="chat-window__bot-header">
        <div class="chat-window__bot-header-info">
          <div class="chat-window__bot-avatar">
            <mat-icon>smart_toy</mat-icon>
          </div>
          <div>
            <span class="chat-window__bot-name">SaiBot</span>
            <span class="chat-window__bot-module">{{ moduleLabel() }}</span>
          </div>
        </div>
        <div class="chat-window__bot-header-actions">
          <button mat-icon-button
                  matTooltip="Limpiar conversación"
                  class="chat-window__clear-btn"
                  (click)="clearBotChat()">
            <mat-icon>delete_sweep</mat-icon>
          </button>
          <span class="chat-window__bot-badge">IA</span>
        </div>
      </div>
    }

    <div class="chat-window__messages"
         #messagesContainer
         [class.chat-window__drop-zone]="isDragOver()"
         (click)="onMessagesClick($event)">
      @if (hasMore()) {
        <button mat-button class="chat-window__load-more" (click)="loadMore()">
          Cargar mensajes anteriores
        </button>
      }

      @for (msg of messages(); track msg.id) {
        <div class="chat-window__msg-row"
             [class.chat-window__msg-row--mine]="msg.remitente === currentUserId()"
             [class.chat-window__msg-row--theirs]="msg.remitente !== currentUserId()"
             (pointerdown)="onSwipeStart($event, msg)">
          <mat-icon class="chat-window__swipe-hint">reply</mat-icon>
          <div class="chat-window__msg"
               [attr.data-msg-id]="msg.id"
               [class.chat-window__msg--mine]="msg.remitente === currentUserId()"
               [class.chat-window__msg--theirs]="msg.remitente !== currentUserId()"
               [class.chat-window__msg--bot]="isBot() && msg.remitente !== currentUserId()">
          @if (msg.responde_a_contenido) {
            <div class="chat-window__reply-preview"
                 (click)="scrollToMessage(msg.responde_a)">
              <mat-icon class="chat-window__reply-preview-icon">reply</mat-icon>
              <div class="chat-window__reply-preview-body">
                @if (msg.responde_a_remitente_nombre) {
                  <span class="chat-window__reply-preview-name">
                    {{ msg.responde_a_remitente_nombre }}
                  </span>
                }
                <span class="chat-window__reply-preview-text">
                  {{ msg.responde_a_contenido }}
                </span>
              </div>
            </div>
          }
          @if (editingMessageId() === msg.id) {
            <div class="chat-window__edit-area">
              <input class="chat-window__edit-input"
                     [ngModel]="editingContent()"
                     (ngModelChange)="editingContent.set($event)"
                     (keydown.enter)="saveEdit(msg.id)"
                     (keydown.escape)="cancelEdit()"
                     autofocus />
              <div class="chat-window__edit-actions">
                <button mat-icon-button (click)="saveEdit(msg.id)" matTooltip="Guardar">
                  <mat-icon>check</mat-icon>
                </button>
                <button mat-icon-button (click)="cancelEdit()" matTooltip="Cancelar">
                  <mat-icon>close</mat-icon>
                </button>
              </div>
            </div>
          } @else {
            @if (msg.contenido_html) {
              <div class="chat-window__content chat-window__content--plain"
                   [class.chat-window__content--emoji]="isSingleEmoji(msg.contenido)"
                   [innerHTML]="sanitize(msg.contenido_html)"></div>
            } @else if (msg.contenido) {
              <div class="chat-window__content chat-window__content--plain"
                   [class.chat-window__content--emoji]="isSingleEmoji(msg.contenido)">{{ msg.contenido }}</div>
            }
          }
          @if (msg.imagen_url) {
            <img class="chat-window__image"
                 loading="lazy"
                 [src]="msg.thumbnail_url || msg.imagen_url"
                 [alt]="'Imagen adjunta'"
                 (click)="openGallery(msg)"
                 (error)="onImgError($event, msg)" />
          }
          @if (msg.archivo_url) {
            <a class="chat-window__file-attachment"
               [href]="msg.archivo_url"
               target="_blank"
               rel="noopener">
              <mat-icon>{{ fileIcon(msg.archivo_nombre ?? '') }}</mat-icon>
              <span>{{ msg.archivo_nombre }}</span>
              <span class="chat-window__file-size">{{ getMsgFileSize(msg) }}</span>
              <mat-icon class="chat-window__download-icon">download</mat-icon>
            </a>
          }
          @if (editingMessageId() !== msg.id) {
            <div class="chat-window__meta">
              @if (msg.editado) {
                <span class="chat-window__edited"
                      [matTooltip]="'Editado ' + (msg.editado_at | date:'short')">
                  (editado)
                </span>
              }
              <span class="chat-window__time">{{ msg.created_at | date:'shortTime' }}</span>
              @if (msg.remitente === currentUserId()) {
                <mat-icon class="chat-window__read-icon"
                          [class.chat-window__read-icon--read]="msg.leido_por_destinatario">
                  {{ msg.leido_por_destinatario ? 'done_all' : 'done' }}
                </mat-icon>
              }
            </div>
          }
          </div>

          @if (isBot() && msg.remitente !== currentUserId() && editingMessageId() !== msg.id) {
            <div class="chat-window__feedback-row">
              <button mat-icon-button
                      class="chat-window__feedback-btn"
                      [class.chat-window__feedback-btn--active]="feedbackMap().get(msg.id) === 1"
                      matTooltip="Útil"
                      (click)="sendFeedback(msg, 1)">
                <mat-icon>thumb_up</mat-icon>
              </button>
              <button mat-icon-button
                      class="chat-window__feedback-btn"
                      [class.chat-window__feedback-btn--active]="feedbackMap().get(msg.id) === -1"
                      matTooltip="No útil"
                      (click)="sendFeedback(msg, -1)">
                <mat-icon>thumb_down</mat-icon>
              </button>
            </div>
          }
        </div>
      } @empty {
        @if (!loadingMessages()) {
          <div class="chat-window__empty">
            @if (isBot()) {
              <mat-icon>smart_toy</mat-icon>
              <p>¡Hola! Soy SaiBot. ¿En qué puedo ayudarte?</p>
              <div class="chat-window__suggestions">
                @for (s of suggestions(); track s) {
                  <button mat-stroked-button
                          class="chat-window__suggestion-chip"
                          (click)="sendSuggestion(s)">
                    {{ s }}
                  </button>
                }
              </div>
            } @else {
              <mat-icon>chat_bubble_outline</mat-icon>
              <p>Inicia la conversacion</p>
            }
          </div>
        }
      }

      @if (typingIndicator()) {
        <div class="chat-window__typing">
          <span class="chat-window__typing-dots">
            <span></span><span></span><span></span>
          </span>
          @if (isBot()) {
            Analizando...
          } @else {
            {{ typingUserName() }} escribiendo...
          }
        </div>
      }
    </div>

    @if (contextMenu()) {
      <div class="chat-window__ctx-backdrop" (click)="closeContextMenu()"></div>
      <div class="chat-window__ctx-menu"
           [style.left.px]="contextMenu()!.x"
           [style.top.px]="contextMenu()!.y">
        <button class="chat-window__ctx-option"
                (click)="startReply(contextMenu()!.msg); closeContextMenu()">
          <mat-icon>reply</mat-icon>
          <span>Responder</span>
        </button>
        @if (canEdit(contextMenu()!.msg)) {
          <button class="chat-window__ctx-option"
                  (click)="startEdit(contextMenu()!.msg); closeContextMenu()">
            <mat-icon>edit</mat-icon>
            <span>Editar</span>
          </button>
        }
      </div>
    }

    <div class="chat-window__input-area">
      @if (uploadStep() !== null) {
        <div class="chat-window__upload-progress">
          <mat-progress-bar mode="indeterminate" />
          <span class="chat-window__upload-label">
            {{ uploadStep() === 'compressing' ? 'Comprimiendo imagen...' : 'Subiendo...' }}
          </span>
        </div>
      }
      @if (pendingFile()) {
        <div class="chat-window__file-preview">
          <mat-icon>{{ fileIcon(pendingFile()!.name) }}</mat-icon>
          <span>{{ pendingFile()!.name }}</span>
          <span class="chat-window__file-size">{{ formatFileSize(pendingFile()!.size) }}</span>
          <button mat-icon-button (click)="clearFile()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      }
      @if (pendingImagePreview()) {
        <div class="chat-window__img-preview">
          <img [src]="pendingImagePreview()!" alt="Preview" class="chat-window__img-preview-thumb" />
          <span class="chat-window__file-size">{{ formatFileSize(pendingImage()!.size) }}</span>
          <button mat-icon-button (click)="clearImage()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      }
      @if (replyingTo()) {
        <div class="chat-window__reply-bar">
          <mat-icon class="chat-window__reply-bar-icon">reply</mat-icon>
          <div class="chat-window__reply-bar-body">
            <span class="chat-window__reply-bar-name">{{ replyingTo()!.remitente_nombre }}</span>
            <span class="chat-window__reply-bar-text">{{ replyPreview() }}</span>
          </div>
          <button mat-icon-button class="chat-window__reply-bar-close" (click)="cancelReply()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      }
      <div class="chat-window__input-row">
        <!-- Hidden file inputs -->
        <input #fileInput type="file"
               accept=".pdf,.docx,.xlsx,.doc,.xls,.pptx,.txt"
               class="chat-window__file-hidden"
               (change)="onFileSelected($event)" />
        <input #imageInput type="file"
               accept="image/jpeg,image/png,image/webp"
               class="chat-window__file-hidden"
               (change)="onImageSelected($event)" />

        <!-- + button with popup menu (hidden for bot conversations) -->
        @if (!isBot()) {
          <div class="chat-window__attach-wrap">
            <button mat-icon-button
                    class="chat-window__attach-btn"
                    [class.chat-window__attach-btn--open]="attachMenuOpen()"
                    (click)="toggleAttachMenu()">
              <mat-icon>add</mat-icon>
            </button>
            @if (attachMenuOpen()) {
              <div class="chat-window__attach-backdrop" (click)="attachMenuOpen.set(false)"></div>
              <div class="chat-window__attach-menu">
                <button class="chat-window__attach-option"
                        (click)="fileInput.click(); attachMenuOpen.set(false)">
                  <mat-icon>attach_file</mat-icon>
                  <span>Archivo</span>
                </button>
                <button class="chat-window__attach-option"
                        (click)="imageInput.click(); attachMenuOpen.set(false)">
                  <mat-icon>image</mat-icon>
                  <span>Imagen</span>
                </button>
              </div>
            }
          </div>
        }

        <app-message-input
          class="chat-window__msg-input"
          [conversacionId]="conversacion().id"
          [hasPendingAttachment]="pendingFile() !== null || pendingImage() !== null"
          (sendMessage)="send($event)"
          (typing)="onTyping()" />
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }

    .chat-window__messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: background 0.2s;
      background-color: var(--sc-surface-ground, #e8edf5);
      background-image: radial-gradient(circle, rgba(0, 0, 0, 0.04) 1.5px, transparent 1.5px);
      background-size: 22px 22px;

      &.chat-window__drop-zone {
        background: var(--sc-primary-50, rgba(21, 101, 192, 0.06));
        outline: 2px dashed var(--sc-primary, #1565c0);
        outline-offset: -4px;
      }
    }

    .chat-window__load-more {
      align-self: center;
      margin-bottom: 8px;
    }

    .chat-window__msg-row {
      display: flex;
      align-items: center;
      position: relative;
      touch-action: pan-y; /* allow vertical scroll, capture horizontal */

      &--mine { justify-content: flex-end; }
      &--theirs { justify-content: flex-start; }
    }

    .chat-window__swipe-hint {
      position: absolute;
      left: 8px;
      top: 50%;
      transform: translateY(-50%) scale(0.5);
      opacity: 0;
      pointer-events: none;
      z-index: 0;
      color: var(--sc-primary, #1565c0);
      font-size: 22px !important;
      width: 22px !important;
      height: 22px !important;
      filter: drop-shadow(0 1px 3px rgba(0,0,0,0.2));
    }

    .chat-window__msg {
      max-width: 80%;
      min-width: 90px;
      padding: 6px 10px 22px;
      border-radius: var(--sc-radius, 10px);
      word-wrap: break-word;
      transition: outline 0.3s ease;
      position: relative;
      z-index: 1;

      &--highlighted {
        outline: 2px solid var(--sc-primary, #1565c0);
        outline-offset: 2px;
      }

      &--mine {
        align-self: flex-end;
        background: var(--sc-primary, #1565c0);
        color: white;
        border-bottom-right-radius: 2px;
      }

      &--theirs {
        align-self: flex-start;
        background: var(--sc-surface-card, #ffffff);
        color: var(--sc-text-color, #1a202c);
        border-bottom-left-radius: 2px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
      }

      &--bot {
        background: var(--sc-primary-50, rgba(21, 101, 192, 0.06));
        border-left: 3px solid var(--sc-primary, #1565c0);
      }
    }

    .chat-window__reply-preview {
      display: flex;
      align-items: flex-start;
      gap: 6px;
      padding: 5px 8px;
      margin-bottom: 6px;
      border-left: 3px solid rgba(255, 255, 255, 0.55);
      background: rgba(0, 0, 0, 0.08);
      border-radius: 0 6px 6px 0;
      cursor: pointer;
      transition: background 0.1s;

      &:hover { background: rgba(0, 0, 0, 0.14); }
    }

    .chat-window__reply-preview-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      flex-shrink: 0;
      margin-top: 2px;
      opacity: 0.8;
    }

    .chat-window__reply-preview-body {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .chat-window__reply-preview-name {
      font-size: 0.72rem;
      font-weight: 600;
      opacity: 0.9;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-window__reply-preview-text {
      font-size: 0.78rem;
      opacity: 0.75;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-window__msg--theirs .chat-window__reply-preview {
      border-left-color: var(--sc-primary, #1565c0);
      background: rgba(21, 101, 192, 0.08);

      &:hover { background: rgba(21, 101, 192, 0.14); }
    }

    .chat-window__reply-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px 6px 10px;
      background: var(--sc-primary-50, rgba(21, 101, 192, 0.08));
      border-left: 3px solid var(--sc-primary, #1565c0);
      border-radius: 4px;
      margin-bottom: 4px;
      animation: reply-bar-in 0.15s ease;
    }

    @keyframes reply-bar-in {
      from { opacity: 0; transform: translateY(4px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .chat-window__reply-bar-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      color: var(--sc-primary, #1565c0);
      flex-shrink: 0;
    }

    .chat-window__reply-bar-body {
      display: flex;
      flex-direction: column;
      flex: 1;
      min-width: 0;
    }

    .chat-window__reply-bar-name {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--sc-primary, #1565c0);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-window__reply-bar-text {
      font-size: 0.8rem;
      color: var(--sc-text-muted, #718096);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .chat-window__reply-bar-close {
      width: 28px !important;
      height: 28px !important;
      line-height: 28px !important;
      flex-shrink: 0;

      mat-icon { font-size: 16px; width: 16px; height: 16px; }
    }

    .chat-window__content {
      line-height: 1.4;
      font-size: 0.9rem;

      &--plain {
        white-space: pre-wrap;
        word-break: break-word;
      }

      &--emoji {
        font-size: 2.6rem;
        line-height: 1.15;
        padding: 2px 0 4px;
        letter-spacing: 2px;
      }
    }

    /* Chip de entidad — inside innerHTML, ::ng-deep required */
    ::ng-deep .chat-entity-link {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 8px 2px 6px;
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.18);
      border: 1px solid rgba(255, 255, 255, 0.35);
      cursor: pointer;
      text-decoration: none;
      color: inherit;
      font-size: 0.8rem;
      vertical-align: middle;
      transition: background 0.15s, border-color 0.15s;
      max-width: 220px;

      &:hover {
        background: rgba(255, 255, 255, 0.28);
        border-color: rgba(255, 255, 255, 0.55);
      }

      &::before {
        content: '🔗';
        font-size: 0.7rem;
        flex-shrink: 0;
      }
    }

    ::ng-deep .chat-entity-link__code {
      font-weight: 700;
      white-space: nowrap;
      flex-shrink: 0;
    }

    ::ng-deep .chat-entity-link__name {
      font-weight: 400;
      opacity: 0.82;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 130px;

      &:not(:empty)::before {
        content: '·';
        margin-right: 3px;
        opacity: 0.6;
      }
    }

    /* Mensajes del peer (fondo claro) — chip oscuro */
    .chat-window__msg--theirs ::ng-deep .chat-entity-link {
      background: rgba(21, 101, 192, 0.1);
      border-color: rgba(21, 101, 192, 0.25);
      color: var(--sc-primary, #1565c0);

      &:hover {
        background: rgba(21, 101, 192, 0.18);
        border-color: rgba(21, 101, 192, 0.4);
      }
    }

    .chat-window__image {
      max-width: 240px;
      max-height: 240px;
      width: 100%;
      object-fit: cover;
      border-radius: 8px;
      margin-top: 4px;
      cursor: pointer;
      display: block;
      transition: opacity 0.15s;

      &:hover { opacity: 0.9; }
    }

    .chat-window__meta {
      position: absolute;
      bottom: 4px;
      right: 8px;
      display: flex;
      align-items: center;
      gap: 3px;
      pointer-events: none;
      white-space: nowrap;
    }

    .chat-window__time {
      font-size: 0.7rem;
      opacity: 0.7;
    }

    .chat-window__read-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      opacity: 0.7;

      &--read {
        opacity: 1;
      }
    }

    .chat-window__typing {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 12px;
      font-size: 0.8rem;
      color: var(--sc-text-muted, #718096);
      font-style: italic;
    }

    .chat-window__typing-dots {
      display: flex;
      gap: 3px;

      span {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--sc-text-muted, #718096);
        animation: bounce-dot 1.4s infinite;

        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
      }
    }

    @keyframes bounce-dot {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }

    .chat-window__empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: var(--sc-text-muted, #718096);

      mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 8px;
      }
    }

    .chat-window__input-area {
      position: relative;
      display: flex;
      flex-direction: column;
      padding: 6px 10px 8px;
      border-top: 1px solid var(--sc-surface-border, #e2e8f0);
      background: var(--sc-surface-card, #fff);
      gap: 4px;
    }

    .chat-window__upload-progress {
      padding: 4px 16px 2px;

      mat-progress-bar { border-radius: 2px; }

      .chat-window__upload-label {
        font-size: 0.75rem;
        color: var(--sc-text-muted, #718096);
      }
    }

    .chat-window__file-preview {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: var(--sc-surface-ground, #f0f2f5);
      border-radius: var(--sc-radius, 8px);
      margin: 0 16px 4px;
      font-size: 0.85rem;

      span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    }

    .chat-window__img-preview {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      margin: 0 16px 4px;
      background: var(--sc-surface-ground, #f0f2f5);
      border-radius: var(--sc-radius, 8px);
    }

    .chat-window__img-preview-thumb {
      width: 56px;
      height: 56px;
      object-fit: cover;
      border-radius: 6px;
      flex-shrink: 0;
    }

    .chat-window__file-size {
      color: var(--sc-text-muted, #718096);
      font-size: 0.75rem;
      flex: 0 !important;
    }

    .chat-window__input-row {
      display: flex;
      align-items: flex-end;
      gap: 4px;
    }

    .chat-window__attach-wrap {
      position: relative;
      flex-shrink: 0;
      align-self: flex-end;
    }

    .chat-window__attach-btn {
      transition: transform 0.2s ease;

      &--open {
        transform: rotate(45deg);
      }
    }

    .chat-window__attach-backdrop {
      position: fixed;
      inset: 0;
      z-index: 100;
    }

    .chat-window__attach-menu {
      position: absolute;
      bottom: calc(100% + 6px);
      left: 0;
      z-index: 101;
      background: var(--sc-surface-card, #fff);
      border: 1px solid var(--sc-surface-border, #e2e8f0);
      border-radius: var(--sc-radius, 10px);
      box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.12);
      overflow: hidden;
      min-width: 160px;
      animation: attach-menu-in 0.15s ease;
    }

    @keyframes attach-menu-in {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .chat-window__attach-option {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      width: 100%;
      border: none;
      background: none;
      cursor: pointer;
      font-size: 0.875rem;
      color: var(--sc-text-color, #1a202c);
      text-align: left;
      transition: background 0.1s;

      &:hover {
        background: var(--sc-surface-hover, rgba(0, 0, 0, 0.06));
      }

      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--sc-text-muted, #718096);
        flex-shrink: 0;
      }
    }

    .chat-window__file-hidden {
      display: none;
    }

    .chat-window__msg-input {
      flex: 1;
    }

    .chat-window__file-attachment {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin-top: 4px;
      background: rgba(0,0,0,0.1);
      border-radius: 8px;
      text-decoration: none;
      color: inherit;
      font-size: 0.85rem;

      mat-icon { font-size: 20px; width: 20px; height: 20px; }

      &:hover { opacity: 0.8; }
    }

    .chat-window__download-icon {
      margin-left: auto;
      opacity: 0.7;
    }

    .chat-window__edit-area {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin: 2px 0;
    }

    .chat-window__edit-input {
      background: rgba(255,255,255,0.2);
      border: 1px solid rgba(255,255,255,0.5);
      border-radius: 4px;
      padding: 4px 8px;
      color: inherit;
      font-size: 0.9rem;
      width: 100%;
      box-sizing: border-box;

      .chat-window__msg--theirs & {
        background: rgba(0,0,0,0.06);
        border-color: var(--sc-surface-border, #e2e8f0);
        color: var(--sc-text-color, #1a202c);
      }

      &:focus { outline: none; }
    }

    .chat-window__edit-actions {
      display: flex;
      gap: 4px;
      justify-content: flex-end;
    }

    .chat-window__edited {
      font-size: 0.65rem;
      opacity: 0.7;
      font-style: italic;
      cursor: default;
    }

    /* ── Bot header ─────────────────────────────────────────────── */
    .chat-window__bot-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 16px;
      background: var(--sc-primary, #1565c0);
      color: white;
      flex-shrink: 0;
      z-index: 2;
    }

    .chat-window__bot-header-info {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .chat-window__bot-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }
    }

    .chat-window__bot-name {
      display: block;
      font-weight: 600;
      font-size: 0.9rem;
      line-height: 1.2;
    }

    .chat-window__bot-module {
      display: block;
      font-size: 0.72rem;
      opacity: 0.8;
      line-height: 1.2;
    }

    .chat-window__bot-header-actions {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .chat-window__clear-btn {
      color: rgba(255,255,255,0.75);
      width: 32px;
      height: 32px;
      line-height: 32px;

      &:hover {
        color: #fff;
        background: rgba(255,255,255,0.15);
      }

      mat-icon { font-size: 20px; width: 20px; height: 20px; }
    }

    .chat-window__bot-badge {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 20px;
      background: rgba(255,255,255,0.25);
      letter-spacing: 0.05em;
    }

    /* ── Feedback buttons ─────────────────────────────────────────── */
    .chat-window__feedback-row {
      display: flex;
      gap: 2px;
      margin-left: 4px;
      align-self: flex-end;
      margin-bottom: 4px;
    }

    .chat-window__feedback-btn {
      width: 28px !important;
      height: 28px !important;
      line-height: 28px !important;
      opacity: 0.45;
      transition: opacity 0.15s, color 0.15s;

      mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
      }

      &:hover { opacity: 0.8; }

      &--active {
        opacity: 1;
        color: var(--sc-primary, #1565c0) !important;
      }
    }

    /* ── Suggestions (empty state bot) ───────────────────────────── */
    .chat-window__suggestions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: center;
      margin-top: 16px;
      padding: 0 16px;
    }

    .chat-window__suggestion-chip {
      font-size: 0.8rem;
      border-radius: 20px !important;
      white-space: normal;
      text-align: left;
      height: auto !important;
      padding: 6px 12px !important;
      line-height: 1.3 !important;
      max-width: 220px;
    }

    /* ── Context menu ───────────────────────────────────────────── */
    .chat-window__ctx-backdrop {
      position: fixed;
      inset: 0;
      z-index: 299;
    }

    .chat-window__ctx-menu {
      position: fixed;
      z-index: 300;
      background: var(--sc-surface-card, #fff);
      border: 1px solid var(--sc-surface-border, #e2e8f0);
      border-radius: var(--sc-radius, 10px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.18);
      overflow: hidden;
      min-width: 160px;
      animation: ctx-menu-in 0.12s ease;
      transform-origin: top center;
    }

    @keyframes ctx-menu-in {
      from { opacity: 0; transform: scale(0.92); }
      to   { opacity: 1; transform: scale(1); }
    }

    .chat-window__ctx-option {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 11px 16px;
      width: 100%;
      border: none;
      background: none;
      cursor: pointer;
      font-size: 0.9rem;
      color: var(--sc-text-color, #1a202c);
      text-align: left;
      transition: background 0.1s;

      &:hover { background: var(--sc-surface-hover, rgba(0, 0, 0, 0.06)); }

      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        color: var(--sc-text-muted, #718096);
        flex-shrink: 0;
      }
    }
  `],
})
export class ChatWindowComponent implements OnInit {
  private readonly chatService = inject(ChatService);
  private readonly chatSocket = inject(ChatSocketService);
  private readonly sanitizer = inject(DomSanitizer);
  private readonly zone = inject(NgZone);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);
  private readonly messagesContainer = viewChild<ElementRef>('messagesContainer');
  private readonly destroyRef = inject(DestroyRef);

  readonly conversacion = input.required<Conversacion>();
  readonly currentUserId = input('');
  readonly jumpToId = input<string | null>(null);
  readonly back = output<void>();

  readonly isBot = computed(() => !!this.conversacion().bot_context);

  private readonly currentUrl = toSignal(
    this.router.events.pipe(filter(e => e instanceof NavigationEnd)),
    { initialValue: null },
  );

  private readonly currentModule = computed(() => {
    // Force dependency on navigation events
    this.currentUrl();
    const url = this.router.url;
    if (url.startsWith('/proyectos'))    return 'proyectos';
    if (url.startsWith('/terceros'))     return 'terceros';
    if (url.startsWith('/saidashboard')) return 'dashboard';
    if (url.startsWith('/contabilidad')) return 'contabilidad';
    // /dashboard es el menú principal → asistente general
    return 'general';
  });

  readonly moduleLabel = computed(() => {
    const ctx = this.currentModule();
    return MODULE_LABELS[ctx] ?? ctx;
  });

  readonly suggestions = computed(() => {
    const ctx = this.currentModule();
    return BOT_SUGGESTIONS[ctx] ?? BOT_SUGGESTIONS['general'];
  });

  // Indicador local de que el bot está procesando (mientras espera respuesta HTTP)
  readonly botThinking = signal(false);

  // Map<mensajeId, rating> para mostrar el estado activo del feedback
  readonly feedbackMap = signal<Map<string, 1 | -1>>(new Map());

  readonly messages = signal<Mensaje[]>([]);
  readonly loadingMessages = signal(false);
  readonly hasMore = signal(false);
  readonly currentPage = signal(1);
  readonly uploadStep = signal<UploadStep>(null);
  readonly pendingFile = signal<File | null>(null);
  readonly pendingImage = signal<File | null>(null);
  readonly pendingImagePreview = signal<string | null>(null);
  readonly isDragOver = signal(false);
  readonly editingMessageId = signal<string | null>(null);
  readonly editingContent = signal('');

  readonly attachMenuOpen = signal(false);
  readonly replyingTo = signal<Mensaje | null>(null);
  readonly contextMenu = signal<{ msg: Mensaje; x: number; y: number } | null>(null);

  readonly replyPreview = computed(() => {
    const msg = this.replyingTo();
    if (!msg) return '';
    const text = msg.contenido || (msg.imagen_url ? '[Imagen]' : msg.archivo_nombre ?? '');
    return text.length > 80 ? text.substring(0, 80) + '...' : text;
  });

  sendFeedback(msg: Mensaje, rating: 1 | -1): void {
    // Optimistic update
    this.feedbackMap.update(map => {
      const next = new Map(map);
      next.set(msg.id, rating);
      return next;
    });
    this.chatService.enviarFeedbackIA({ mensaje_id: msg.id, rating }).subscribe({
      error: () => {
        // Revert on error
        this.feedbackMap.update(map => {
          const next = new Map(map);
          next.delete(msg.id);
          return next;
        });
        this.snackBar.open('No se pudo guardar el feedback', 'OK', { duration: 3000 });
      },
    });
  }

  sendSuggestion(text: string): void {
    this.send(text);
  }

  clearBotChat(): void {
    this.chatService.limpiarChatBot().subscribe({
      next: () => {
        this.messages.set([]);
        this.snackBar.open('Conversación limpiada', 'OK', {
          duration: 2500,
          panelClass: ['snack-success'],
        });
      },
      error: () => {
        this.snackBar.open('No se pudo limpiar la conversación', 'OK', { duration: 3000 });
      },
    });
  }

  toggleAttachMenu(): void {
    this.attachMenuOpen.update(open => !open);
  }

  startReply(msg: Mensaje): void {
    this.replyingTo.set(msg);
  }

  cancelReply(): void {
    this.replyingTo.set(null);
  }

  showContextMenu(msg: Mensaje, x: number, y: number): void {
    // Clamp so menu doesn't go off-screen right/bottom
    const menuW = 180;
    const menuH = this.canEdit(msg) ? 96 : 48;
    const cx = Math.min(x, window.innerWidth - menuW - 8);
    const cy = Math.min(y, window.innerHeight - menuH - 8);
    this.contextMenu.set({ msg, x: cx, y: cy });
  }

  closeContextMenu(): void {
    this.contextMenu.set(null);
  }

  scrollToMessage(msgId: string | null): void {
    if (!msgId) return;
    const el = document.querySelector(`[data-msg-id="${msgId}"]`) as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('chat-window__msg--highlighted');
      setTimeout(() => el.classList.remove('chat-window__msg--highlighted'), 2000);
    }
  }

  readonly typingIndicator = computed(() => {
    // Para bots: usar el indicador local (el bot no emite eventos WS de typing)
    if (this.isBot()) return this.botThinking();
    const evt = this.chatSocket.typingEvent();
    if (!evt) return false;
    return evt.conversacion_id === this.conversacion().id &&
           evt.user_id !== this.currentUserId();
  });

  readonly typingUserName = computed(() => {
    const evt = this.chatSocket.typingEvent();
    return evt?.user_name ?? '';
  });

  /** All full-res image URLs in current message list, for gallery navigation. */
  private get galleryImages(): string[] {
    return this.messages()
      .filter(m => !!m.imagen_url)
      .map(m => m.imagen_url);
  }

  private typingThrottle: ReturnType<typeof setTimeout> | null = null;
  private readonly sanitizedCache = new Map<string, SafeHtml>();

  constructor() {
    this.chatSocket.newMessage$.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(msg => {
      if (msg.conversacion !== this.conversacion().id) return;
      if (!this.messages().some(m => m.id === msg.id)) {
        this.messages.update(msgs => [...msgs, msg]);
        this.cdr.markForCheck();
      }
      // Si el bot respondió, apagar el indicador de "pensando"
      if (this.isBot() && msg.remitente !== this.currentUserId()) {
        this.botThinking.set(false);
      }
      this.scrollToBottom();
      if (msg.remitente !== this.currentUserId()) {
        this.chatSocket.markRead(msg.id);
      }
    });

    this.chatSocket.readEvent$.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(evt => {
      this.messages.update(msgs =>
        msgs.map(m => m.id === evt.mensaje_id
          ? { ...m, leido_por_destinatario: true, leido_at: evt.leido_at }
          : m
        )
      );
      this.cdr.markForCheck();
    });

    toObservable(this.typingIndicator).pipe(
      filter(v => v === true),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(() => this.scrollToBottom());

    // Real-time message edits from other participants
    this.chatSocket.messageEdited$.pipe(
      takeUntilDestroyed(this.destroyRef),
    ).subscribe((evt: ChatMessageEditedEvent) => {
      this.messages.update(msgs =>
        msgs.map(m => m.id === evt.mensaje_id
          ? { ...m, contenido: evt.contenido, contenido_html: evt.contenido_html,
              editado: true, editado_at: evt.editado_at }
          : m
        )
      );
      this.cdr.markForCheck();
    });

    toObservable(this.jumpToId).pipe(
      filter((id): id is string => id !== null),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(id => {
      setTimeout(() => {
        const el = document.querySelector(`[data-msg-id="${id}"]`) as HTMLElement | null;
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          el.classList.add('chat-window__msg--highlighted');
          setTimeout(() => el.classList.remove('chat-window__msg--highlighted'), 2000);
        }
      }, 100);
    });
  }

  ngOnInit(): void {
    this.loadMessages();
  }

  sanitize(html: string): SafeHtml {
    if (!this.sanitizedCache.has(html)) {
      this.sanitizedCache.set(html, this.sanitizer.bypassSecurityTrustHtml(html));
    }
    return this.sanitizedCache.get(html)!;
  }

  loadMessages(): void {
    this.loadingMessages.set(true);
    this.chatService.listarMensajes(this.conversacion().id, 1).subscribe({
      next: (res) => {
        // API returns newest-first; reverse for display (oldest at top, newest at bottom)
        this.messages.set([...res.results].reverse());
        this.hasMore.set(!!res.next);
        this.currentPage.set(1);
        this.loadingMessages.set(false);
        this.scrollToBottom();
        res.results
          .filter(m => m.remitente !== this.currentUserId() && !m.leido_por_destinatario)
          .forEach(m => this.chatSocket.markRead(m.id));
      },
      error: () => this.loadingMessages.set(false),
    });
  }

  loadMore(): void {
    const nextPage = this.currentPage() + 1;
    this.chatService.listarMensajes(this.conversacion().id, nextPage).subscribe({
      next: (res) => {
        // Older messages (next page) go above current messages
        this.messages.update(msgs => [...res.results.reverse(), ...msgs]);
        this.hasMore.set(!!res.next);
        this.currentPage.set(nextPage);
      },
    });
  }

  send(text: string): void {
    const trimmed = text.trim();
    const file = this.pendingFile();
    const image = this.pendingImage();

    if (!trimmed && !file && !image) return;

    const responde_a_id = this.replyingTo()?.id;
    this.cancelReply();

    if (image) {
      this.uploadImage(image, trimmed, responde_a_id);
    } else if (file) {
      this.uploadFile(file, trimmed, responde_a_id);
    } else {
      if (this.isBot()) this.botThinking.set(true);
      this.chatService.enviarMensaje(this.conversacion().id, {
        contenido: trimmed,
        responde_a_id,
      }).subscribe({
        next: (msg) => {
          this.messages.update(msgs => [...msgs, msg]);
          this.scrollToBottom();
        },
      });
    }
  }

  private uploadFile(file: File, texto: string, responde_a_id?: string): void {
    this.uploadStep.set('uploading');
    this.chatService.uploadArchivo(file).subscribe({
      next: (res) => {
        this.uploadStep.set(null);
        this.pendingFile.set(null);
        this.chatService.enviarMensaje(this.conversacion().id, {
          contenido: texto || res.archivo_nombre,
          archivo_url: res.archivo_url,
          archivo_nombre: res.archivo_nombre,
          archivo_tamaño: res.archivo_tamaño,
          responde_a_id,
        }).subscribe({
          next: (msg) => {
            this.messages.update(msgs => [...msgs, msg]);
            this.scrollToBottom();
          },
        });
      },
      error: () => this.uploadStep.set(null),
    });
  }

  private uploadImage(file: File, texto: string, responde_a_id?: string): void {
    this.uploadStep.set('compressing');
    compressImage(file).then(blob => {
      this.uploadStep.set('uploading');
      const ext = compressedExtension(file);
      const name = file.name.replace(/\.[^.]+$/, '') + ext;
      this.chatService.uploadImagen(blob, name).subscribe({
        next: (res) => {
          this.uploadStep.set(null);
          this.clearImage();
          this.chatService.enviarMensaje(this.conversacion().id, {
            contenido: texto,
            imagen_url: res.imagen_url,
            thumbnail_url: res.thumbnail_url,
            responde_a_id,
          }).subscribe({
            next: (msg) => {
              this.messages.update(msgs => [...msgs, msg]);
              this.scrollToBottom();
            },
          });
        },
        error: () => {
          this.uploadStep.set(null);
          this.cdr.markForCheck();
        },
      });
    }).catch(() => {
      this.uploadStep.set(null);
      this.cdr.markForCheck();
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    input.value = '';
    this.clearImage();
    this.pendingFile.set(file);
  }

  onImageSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    input.value = '';
    if (!file) return;
    this.clearFile();
    this.setImagePreview(file);
  }

  clearFile(): void {
    this.pendingFile.set(null);
  }

  clearImage(): void {
    const prev = this.pendingImagePreview();
    if (prev) URL.revokeObjectURL(prev);
    this.pendingImage.set(null);
    this.pendingImagePreview.set(null);
  }

  private setImagePreview(file: File): void {
    const prev = this.pendingImagePreview();
    if (prev) URL.revokeObjectURL(prev);
    this.pendingImage.set(file);
    this.pendingImagePreview.set(URL.createObjectURL(file));
  }

  // ── Edición ───────────────────────────────────────────────────────

  canEdit(msg: Mensaje): boolean {
    if (msg.remitente !== this.currentUserId()) return false;
    const ageMs = Date.now() - new Date(msg.created_at).getTime();
    return ageMs < 15 * 60 * 1000;
  }

  startEdit(msg: Mensaje): void {
    this.editingMessageId.set(msg.id);
    this.editingContent.set(msg.contenido);
  }

  cancelEdit(): void {
    this.editingMessageId.set(null);
    this.editingContent.set('');
  }

  saveEdit(mensajeId: string): void {
    const contenido = this.editingContent().trim();
    if (!contenido) return;
    this.chatService.editarMensaje(mensajeId, contenido).subscribe({
      next: (updated) => {
        this.messages.update(msgs =>
          msgs.map(m => m.id === mensajeId ? { ...m, ...updated } : m)
        );
        this.editingMessageId.set(null);
        this.editingContent.set('');
        this.cdr.markForCheck();
      },
    });
  }

  // ── Drag & drop ───────────────────────────────────────────────────

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver.set(false);
    const file = event.dataTransfer?.files?.[0] ?? null;
    if (!file) return;
    if (file.type.startsWith('image/')) {
      this.clearFile();
      this.setImagePreview(file);
    } else {
      this.clearImage();
      this.pendingFile.set(file);
    }
  }

  // ── Gallery ───────────────────────────────────────────────────────

  openGallery(msg: Mensaje): void {
    const images = this.galleryImages;
    const initialIndex = images.indexOf(msg.imagen_url);
    this.dialog.open<ImageViewerDialogComponent, ImageViewerData>(
      ImageViewerDialogComponent,
      {
        data: { images, initialIndex: initialIndex >= 0 ? initialIndex : 0 },
        panelClass: 'image-viewer-panel',
        maxWidth: '95vw',
        maxHeight: '95vh',
      },
    );
  }

  onImgError(event: Event, msg: Mensaje): void {
    // Thumbnail failed — fallback to original
    const img = event.target as HTMLImageElement;
    if (img.src !== msg.imagen_url) {
      img.src = msg.imagen_url;
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────

  isSingleEmoji(text: string): boolean {
    if (!text?.trim()) return false;
    const trimmed = text.trim();
    if (trimmed.length > 14) return false;
    try {
      const segments = [...new Intl.Segmenter().segment(trimmed)].map(s => s.segment);
      if (segments.length === 0 || segments.length > 3) return false;
      const emojiRe = /^\p{Extended_Pictographic}/u;
      return segments.every(s => emojiRe.test(s));
    } catch {
      return false;
    }
  }

  fileIcon(name: string): string {
    const ext = name.split('.').pop()?.toLowerCase() ?? '';
    if (ext === 'pdf') return 'picture_as_pdf';
    if (['xlsx', 'xls'].includes(ext)) return 'table_chart';
    if (['docx', 'doc'].includes(ext)) return 'description';
    return 'insert_drive_file';
  }

  formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  getMsgFileSize(msg: Mensaje): string {
    const bytes = (msg as unknown as Record<string, unknown>)['archivo_tama\u00f1o'] as number | undefined;
    return this.formatFileSize(bytes ?? 0);
  }

  onTyping(): void {
    if (this.typingThrottle) return;
    this.chatSocket.sendTyping(this.conversacion().id);
    this.typingThrottle = setTimeout(() => {
      this.typingThrottle = null;
    }, 3000);
  }

  onMessagesClick(event: MouseEvent): void {
    // setPointerCapture() in onSwipeStart redirects click's target to the row element,
    // so event.target.closest() won't find the <a>. composedPath() contains the full
    // original path from innermost element to document, working around this.
    const link = (event.composedPath() as Element[]).find(
      (el): el is HTMLAnchorElement =>
        el instanceof HTMLAnchorElement && el.classList.contains('chat-entity-link'),
    );
    if (!link) return;
    event.preventDefault();
    const href = link.getAttribute('href');
    if (href) {
      this.router.navigateByUrl(href);
      this.back.emit();
    }
  }

  // ── Swipe-to-reply + Long press context menu ─────────────────────

  private readonly SWIPE_THRESHOLD = 65;
  private swipeState: {
    startX: number;
    startY: number;
    msgEl: HTMLElement;
    iconEl: HTMLElement | null;
    triggered: boolean;
  } | null = null;
  private longPressTimer: ReturnType<typeof setTimeout> | null = null;

  onSwipeStart(event: PointerEvent, msg: Mensaje): void {
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    if (this.editingMessageId() !== null) return;

    const rowEl = event.currentTarget as HTMLElement;
    const msgEl = rowEl.querySelector('.chat-window__msg') as HTMLElement | null;
    if (!msgEl) return;

    rowEl.setPointerCapture(event.pointerId);
    const iconEl = rowEl.querySelector('.chat-window__swipe-hint') as HTMLElement | null;

    this.swipeState = {
      startX: event.clientX,
      startY: event.clientY,
      msgEl,
      iconEl,
      triggered: false,
    };

    let longPressTriggered = false;
    const startX = event.clientX;
    const startY = event.clientY;

    // Long press: 500ms without significant movement
    this.longPressTimer = setTimeout(() => {
      longPressTriggered = true;
      this.snapBack();
      cleanup();
      navigator.vibrate?.(20);
      this.zone.run(() => this.showContextMenu(msg, startX, startY));
    }, 500);

    const onMove = (e: PointerEvent): void => {
      if (!this.swipeState) return;
      const dx = e.clientX - this.swipeState.startX;
      const dy = e.clientY - this.swipeState.startY;

      // Cancel long press if moved more than 8px
      if ((Math.abs(dx) > 8 || Math.abs(dy) > 8) && this.longPressTimer) {
        clearTimeout(this.longPressTimer);
        this.longPressTimer = null;
      }

      // Cancel swipe if predominantly vertical
      if (Math.abs(dy) > Math.abs(dx) * 1.5 && Math.abs(dx) < 8) {
        this.snapBack();
        return;
      }
      if (dx <= 0) return;

      // Rubber-band resistance past threshold
      const capped = dx < this.SWIPE_THRESHOLD
        ? dx
        : this.SWIPE_THRESHOLD + (dx - this.SWIPE_THRESHOLD) * 0.15;

      this.swipeState.msgEl.style.transform = `translateX(${capped}px)`;

      const icon = this.swipeState.iconEl;
      if (icon) {
        const p = Math.min(dx / this.SWIPE_THRESHOLD, 1);
        icon.style.opacity = String(p);
        icon.style.transform = `translateY(-50%) scale(${0.5 + p * 0.5})`;

        if (dx >= this.SWIPE_THRESHOLD && !this.swipeState.triggered) {
          this.swipeState.triggered = true;
          navigator.vibrate?.(12);
          icon.style.transform = 'translateY(-50%) scale(1.25)';
          setTimeout(() => {
            if (icon) icon.style.transform = 'translateY(-50%) scale(1)';
          }, 140);
        }
      }
    };

    const onEnd = (): void => {
      if (this.longPressTimer) {
        clearTimeout(this.longPressTimer);
        this.longPressTimer = null;
      }
      if (longPressTriggered) { cleanup(); return; }
      if (!this.swipeState) { cleanup(); return; }
      const triggered = this.swipeState.triggered;
      const capturedMsg = msg;
      this.snapBack();
      cleanup();
      if (triggered) {
        this.zone.run(() => this.startReply(capturedMsg));
      }
    };

    const cleanup = (): void => {
      rowEl.removeEventListener('pointermove', onMove as EventListener);
      rowEl.removeEventListener('pointerup', onEnd);
      rowEl.removeEventListener('pointercancel', onEnd);
    };

    this.zone.runOutsideAngular(() => {
      rowEl.addEventListener('pointermove', onMove as EventListener);
      rowEl.addEventListener('pointerup', onEnd);
      rowEl.addEventListener('pointercancel', onEnd);
    });
  }

  private snapBack(): void {
    if (!this.swipeState) return;
    const { msgEl, iconEl } = this.swipeState;
    this.swipeState = null;

    msgEl.style.transition = 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
    msgEl.style.transform = 'translateX(0)';
    setTimeout(() => { msgEl.style.transition = ''; }, 310);

    if (iconEl) {
      iconEl.style.transition = 'opacity 0.2s, transform 0.2s';
      iconEl.style.opacity = '0';
      iconEl.style.transform = 'translateY(-50%) scale(0.5)';
      setTimeout(() => { iconEl.style.transition = ''; }, 210);
    }
  }

  private scrollToBottom(): void {
    this.zone.runOutsideAngular(() => {
      setTimeout(() => {
        const el = this.messagesContainer()?.nativeElement as HTMLElement | undefined;
        if (el) el.scrollTop = el.scrollHeight;
      }, 50);
    });
  }
}
