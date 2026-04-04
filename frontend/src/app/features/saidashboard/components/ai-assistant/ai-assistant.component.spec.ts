import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { AiAssistantComponent } from './ai-assistant.component';

describe('AiAssistantComponent', () => {
  let fixture: ComponentFixture<AiAssistantComponent>;
  let component: AiAssistantComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [AiAssistantComponent, HttpClientTestingModule, NoopAnimationsModule],
    });
    fixture   = TestBed.createComponent(AiAssistantComponent);
    component = fixture.componentInstance;
    http      = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('starts closed', () => {
    expect(component.isOpen()).toBeFalse();
  });

  it('toggle() opens and closes the panel', () => {
    component.toggle();
    expect(component.isOpen()).toBeTrue();
    component.toggle();
    expect(component.isOpen()).toBeFalse();
  });

  it('sendMessage() does nothing when input is empty', () => {
    component.inputText.set('');
    component.sendMessage();
    http.expectNone('/api/v1/dashboard/cfo-virtual/');
    expect(component.messages().length).toBe(0);
  });

  it('sendMessage() adds user message and calls API', () => {
    component.inputText.set('Como esta mi liquidez?');
    component.sendMessage();

    expect(component.messages().length).toBe(1);
    expect(component.messages()[0].role).toBe('user');
    expect(component.loading()).toBeTrue();

    const req = http.expectOne('/api/v1/dashboard/cfo-virtual/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.question).toBe('Como esta mi liquidez?');
    req.flush({ response: 'Tu liquidez es buena.' });

    expect(component.loading()).toBeFalse();
    expect(component.messages().length).toBe(2);
    expect(component.messages()[1].role).toBe('assistant');
    expect(component.messages()[1].content).toBe('Tu liquidez es buena.');
  });

  it('sendMessage() shows error message on API failure', () => {
    component.inputText.set('Pregunta');
    component.sendMessage();

    const req = http.expectOne('/api/v1/dashboard/cfo-virtual/');
    req.flush('Error', { status: 502, statusText: 'Bad Gateway' });

    expect(component.loading()).toBeFalse();
    expect(component.messages()[1].role).toBe('assistant');
    expect(component.messages()[1].content).toContain('Lo siento');
  });

  it('sendMessage(text) sends quick action text directly', () => {
    component.sendMessage('Resumen financiero del mes');
    expect(component.messages()[0].content).toBe('Resumen financiero del mes');
    http.expectOne('/api/v1/dashboard/cfo-virtual/').flush({ response: 'OK' });
  });

  it('clears inputText after sending', () => {
    component.inputText.set('Hola');
    component.sendMessage();
    expect(component.inputText()).toBe('');
    http.expectOne('/api/v1/dashboard/cfo-virtual/').flush({ response: 'OK' });
  });

  it('quickActions has 4 items', () => {
    expect(component.quickActions.length).toBe(4);
  });
});
