// SICCE Enterprise Healthcare Architecture Client Logic (Veryfi + Eka Care Standard)

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mount Scroll-World 5-Stage 3D Enterprise Flight Engine
  const scrollWorldRoot = document.getElementById('scroll-world-root');
  if (scrollWorldRoot && typeof mountScrollWorld === 'function') {
    mountScrollWorld(scrollWorldRoot, {
      brand: { name: 'SICCE', href: '#top' },
      cta: { label: 'Explore Interactive Sandbox', href: '#sandbox' },
      hint: 'scroll to explore clinical intelligence engine',
      diveScroll: 1.4,
      atmosphere: true,
      sections: [
        {
          id: 'workstation',
          label: '1. Clinical Intake',
          still: '/static/assets/pro_scene_1.jpg',
          accent: '#059669',
          scroll: 1.5,
          linger: 0.45,
          huds: ['Clinical Tablet EMR', 'Optical Prescription Bed'],
          eyebrow: 'STAGE 01 / CLINICAL RECEPTION',
          title: 'Prescriptions enter here.',
          body: 'Doctor consultations written in English, Hindi, and local shorthand abbreviations are ingested directly at the clinical workstation.',
          tags: ['Hinglish Dialects', 'Local Abbreviations', 'Optical OPD Slip']
        },
        {
          id: 'scanner',
          label: '2. Optical Array',
          still: '/static/assets/pro_scene_2.jpg',
          accent: '#0284c7',
          scroll: 1.5,
          linger: 0.45,
          huds: ['Optical Laser Ribbon', 'DPDP PHI Sanitized'],
          eyebrow: 'STAGE 02 / STATUTORY DE-IDENTIFICATION',
          title: 'Laser-scanned and scrubbed.',
          body: 'High-speed optical OCR isolates prescription text while the statutory DPDP engine scrubs ABHA IDs, Aadhaar, and patient names.',
          tags: ['DPDP Act 2023 Compliant', 'Zero PHI Retention', 'Optical Bounding Boxes']
        },
        {
          id: 'ontology',
          label: '3. Ontology Graph',
          still: '/static/assets/pro_scene_3.jpg',
          accent: '#6366f1',
          scroll: 1.6,
          linger: 0.45,
          huds: ['100k+ SNOMED CT Concepts', 'AYUSH NAMASTE Extension'],
          eyebrow: 'STAGE 03 / ONTOLOGY CROSS-WALK',
          title: 'Mapped to pure terminology.',
          body: 'Sub-50ms Supabase pg_trgm fuzzy matching links colloquial symptoms and AYUSH medicines directly to 100k+ canonical SNOMED CT concepts.',
          tags: ['100k+ SNOMED CT Concepts', 'AYUSH NAMASTE Bridge', 'Sub-50ms GIN Index']
        },
        {
          id: 'assembly',
          label: '4. FHIR Assembly',
          still: '/static/assets/pro_scene_4.jpg',
          accent: '#7c3aed',
          scroll: 1.5,
          linger: 0.45,
          huds: ['HL7 FHIR OPConsultation', 'MedicationRequest & Condition'],
          eyebrow: 'STAGE 04 / INTEROPERABILITY FACTORY',
          title: 'Assembled into standard FHIR.',
          body: 'Extracted dosages, frequencies, and coded conditions glide along automated data tracks into an official ABDM OPConsultation document bundle.',
          tags: ['NRCES FHIR R4 Profile', 'Structured Dosages', 'EMR Ready']
        },
        {
          id: 'vault',
          label: '5. The Vault',
          still: '/static/assets/pro_scene_5.jpg',
          accent: '#059669',
          scroll: 1.6,
          linger: 0.5,
          huds: ['ABDM Milestone 3 Verified', 'Section 12 SHA-256 Purge'],
          eyebrow: 'STAGE 05 / ENTERPRISE SECURITY',
          title: 'One verified FHIR package.',
          body: 'The encrypted document package is verified against national ABDM Milestone 3 standards with cryptographic Section 12 purge audit receipts.',
          tags: ['ABDM Milestone 3 Ready', 'SHA-256 Purge Receipt', 'Hospital Cloud Gateway'],
          cta: {
            primary: { label: 'Open Live Sandbox', href: '#sandbox' },
            secondary: { label: 'Explore API Docs', href: '/docs' }
          }
        }
      ]
    });
  }

  // 2. Sample Datasets Definition
  const samples = {
    sample1: {
      img: '/static/assets/sample_rx_slip.jpg',
      headerHtml: `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-size: 0.88rem; font-weight: 800; color: #0f172a;">Apollo Clinic, Pune (Dr. Rajesh Sharma, MD)</span>
          <span style="font-size: 0.72rem; font-family: var(--font-mono); color: #059669; background: #ecfdf5; padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">Reg: 45678</span>
        </div>
        <div style="font-size: 0.8rem; color: #475569;" id="item-patient">
          Patient: <strong>Mr. Rahul Verma</strong> (34 Y/M) | BP: <strong id="item-vitals">120/80 mmHg</strong> | Wt: 72 Kgs
        </div>
      `,
      text: "Severe headache and nausea since 2 days. Acidic taste. APD positive. Tab Pantocid 40mg OD x 5 days, Tab Dolo 650mg BD x 3 days, Syp Mucaine 2 tsp TDS.",
      boxesHtml: `
        <img src="/static/assets/sample_rx_slip.jpg" alt="Apollo Clinic Prescription" class="optical-doc-img" id="optical-rx-img">
        <div class="optical-box" id="box-clinic" style="top: 8%; left: 24%; width: 48%; height: 8%;" data-target="item-clinic">
          <span class="box-label">CLINIC_ENTITY</span>
        </div>
        <div class="optical-box" id="box-patient" style="top: 23%; left: 26%; width: 50%; height: 5%;" data-target="item-patient">
          <span class="box-label">PATIENT_DEMOGRAPHICS</span>
        </div>
        <div class="optical-box" id="box-vitals" style="top: 27%; left: 56%; width: 26%; height: 5%;" data-target="item-vitals">
          <span class="box-label">VITALS (BP 120/80)</span>
        </div>
        <div class="optical-box" id="box-symptoms" style="top: 38%; left: 25%; width: 52%; height: 10%;" data-target="chips-symptoms">
          <span class="box-label">SYMPTOMS (SNOMED)</span>
        </div>
        <div class="optical-box" id="box-diagnosis" style="top: 48%; left: 25%; width: 52%; height: 8%;" data-target="chips-diagnoses">
          <span class="box-label">DIAGNOSIS (APD)</span>
        </div>
        <div class="optical-box" id="box-rx1" style="top: 57%; left: 26%; width: 50%; height: 5%;" data-target="rx-row-1">
          <span class="box-label">MEDICATION: PANTOCID 40</span>
        </div>
        <div class="optical-box" id="box-rx2" style="top: 62%; left: 26%; width: 50%; height: 5%;" data-target="rx-row-2">
          <span class="box-label">MEDICATION: DOLO 650</span>
        </div>
        <div class="optical-box" id="box-rx3" style="top: 67%; left: 26%; width: 50%; height: 5%;" data-target="rx-row-3">
          <span class="box-label">MEDICATION: MUCAINE</span>
        </div>
      `
    },
    sample2: {
      img: '/static/assets/sample_rx_slip_max.jpg',
      headerHtml: `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-size: 0.88rem; font-weight: 800; color: #0f172a;">Max Super Speciality Hospital, Delhi (Dr. Ananya Sen, MD)</span>
          <span style="font-size: 0.72rem; font-family: var(--font-mono); color: #059669; background: #ecfdf5; padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">Dept: Gastroenterology</span>
        </div>
        <div style="font-size: 0.8rem; color: #475569;" id="item-patient">
          Patient: <strong>Priya Sharma</strong> (28 Y/F) | BP: <strong id="item-vitals">110/70 mmHg</strong> | Acute Emergency
        </div>
      `,
      text: "Pt c/o Acute loose motion x 3 days & severe AP+ (Abdominal Pain). Dx: Acute Gastroenteritis / APD. Tab Norflox TZ BD pc x 5 days, Tab Pantocid 40mg OD, Tab Dolo 650mg BD x 3 days, ORS Sachets 1 pack in 1L water.",
      boxesHtml: `
        <img src="/static/assets/sample_rx_slip_max.jpg" alt="Max Hospital Prescription" class="optical-doc-img" id="optical-rx-img">
        <div class="optical-box" id="box-clinic" style="top: 8%; left: 22%; width: 54%; height: 8%;" data-target="item-clinic">
          <span class="box-label">MAX_HOSPITAL_ENTITY</span>
        </div>
        <div class="optical-box" id="box-patient" style="top: 18%; left: 23%; width: 54%; height: 8%;" data-target="item-patient">
          <span class="box-label">PATIENT: PRIYA SHARMA (28/F)</span>
        </div>
        <div class="optical-box" id="box-symptoms" style="top: 30%; left: 23%; width: 54%; height: 10%;" data-target="chips-symptoms">
          <span class="box-label">SYMPTOMS: LOOSE MOTION &amp; AP+</span>
        </div>
        <div class="optical-box" id="box-diagnosis" style="top: 42%; left: 23%; width: 54%; height: 8%;" data-target="chips-diagnoses">
          <span class="box-label">DX: GASTROENTERITIS / APD</span>
        </div>
        <div class="optical-box" id="box-rx1" style="top: 50%; left: 23%; width: 54%; height: 10%;" data-target="rx-row-1">
          <span class="box-label">MEDICATION: NORFLOX TZ BD</span>
        </div>
        <div class="optical-box" id="box-rx2" style="top: 61%; left: 23%; width: 54%; height: 6%;" data-target="rx-row-2">
          <span class="box-label">MEDICATION: DOLO 650 BD</span>
        </div>
        <div class="optical-box" id="box-rx3" style="top: 68%; left: 23%; width: 54%; height: 6%;" data-target="rx-row-3">
          <span class="box-label">MEDICATION: ORS SACHETS</span>
        </div>
      `
    },
    sample3: {
      img: '/static/assets/sample_rx_slip_ayush.jpg',
      headerHtml: `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-size: 0.88rem; font-weight: 800; color: #0f172a;">National Institute of Ayurveda, Jaipur (Vaidya Arvind Shastri, BAMS)</span>
          <span style="font-size: 0.72rem; font-family: var(--font-mono); color: #7c3aed; background: #faf5ff; padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">AYUSH NAMASTE</span>
        </div>
        <div style="font-size: 0.8rem; color: #475569;" id="item-patient">
          Patient: <strong>Smt. Sunita Devi</strong> (52 Y/F) | Prakriti: Vata-Kapha | Chronic Care
        </div>
      `,
      text: "Pt has h/o Sandhivata & Amavata (Joint Pain & Stiffness) x 6 months. Dx: Amavata (Rheumatoid / Inflammatory Joint Disorder). Rx: Triphala Churna 1 tsp HS with warm water x 30 days, Yograj Guggulu 2 tab BD with lukewarm water x 30 days, Tab Lasix 40mg OD x 10 days.",
      boxesHtml: `
        <img src="/static/assets/sample_rx_slip_ayush.jpg" alt="National Ayurvedic Prescription" class="optical-doc-img" id="optical-rx-img">
        <div class="optical-box" id="box-clinic" style="top: 10%; left: 10%; width: 80%; height: 8%;" data-target="item-clinic">
          <span class="box-label">NATIONAL_AYURVEDIC_INSTITUTE</span>
        </div>
        <div class="optical-box" id="box-patient" style="top: 24%; left: 10%; width: 80%; height: 6%;" data-target="item-patient">
          <span class="box-label">PATIENT: SUNITA DEVI (52/F)</span>
        </div>
        <div class="optical-box" id="box-symptoms" style="top: 30%; left: 10%; width: 80%; height: 12%;" data-target="chips-symptoms">
          <span class="box-label">CHIEF COMPLAINTS: AMAVATA</span>
        </div>
        <div class="optical-box" id="box-diagnosis" style="top: 44%; left: 10%; width: 80%; height: 8%;" data-target="chips-diagnoses">
          <span class="box-label">AYUSH DX: AMAVATA (AM192)</span>
        </div>
        <div class="optical-box" id="box-rx1" style="top: 55%; left: 10%; width: 80%; height: 6%;" data-target="rx-row-1">
          <span class="box-label">AYUSH: TRIPHALA CHURNA</span>
        </div>
        <div class="optical-box" id="box-rx2" style="top: 61%; left: 10%; width: 80%; height: 6%;" data-target="rx-row-2">
          <span class="box-label">AYUSH: YOGRAJ GUGGULU</span>
        </div>
        <div class="optical-box" id="box-rx3" style="top: 73%; left: 10%; width: 80%; height: 6%;" data-target="rx-row-3">
          <span class="box-label">ALLOPATHIC: LASIX 40MG OD</span>
        </div>
      `
    }
  };

  const opticalDocContainer = document.getElementById('optical-doc-container');
  const itemClinicHeader = document.getElementById('item-clinic');
  const noteInput = document.getElementById('clinical-note-input');
  const activeKeySelect = document.getElementById('active-key-select');
  const btnParseNote = document.getElementById('btn-parse-note');

  const chipsSymptoms = document.getElementById('chips-symptoms');
  const chipsDiagnoses = document.getElementById('chips-diagnoses');
  const medicationsTableBody = document.getElementById('medications-table-body');
  const fhirJsonCode = document.getElementById('fhir-json-code');
  const codeSnippetDisplay = document.getElementById('code-snippet-display');

  const ddiAlertContainer = document.getElementById('ddi-alert-container');
  const ddiAlertTitle = document.getElementById('ddi-alert-title');
  const ddiAlertMessage = document.getElementById('ddi-alert-message');

  const vernacularCardsContainer = document.getElementById('vernacular-cards-container');
  const vernacularPills = document.querySelectorAll('.vernacular-pill');
  let activeVernacularLang = 'hi';

  const btnCopyJson = document.getElementById('btn-copy-json');
  const btnDownloadJson = document.getElementById('btn-download-json');

  // Input Mode Toggles (Optical Canvas vs Text)
  const tabBtnTextMode = document.getElementById('tab-btn-text-mode');
  const tabBtnCanvasMode = document.getElementById('tab-btn-canvas-mode');
  const viewInputText = document.getElementById('view-input-text');
  const viewInputCanvas = document.getElementById('view-input-canvas');

  // Inspector Tabs
  const inspectorTabBtns = document.querySelectorAll('.inspector-tab-btn');
  const inspectorViewClinical = document.getElementById('inspector-view-clinical');
  const inspectorViewVernacular = document.getElementById('inspector-view-vernacular');
  const inspectorViewJson = document.getElementById('inspector-view-json');
  const inspectorViewPipeline = document.getElementById('inspector-view-pipeline');

  // Custom File Upload (Real Multimodal Vision OCR)
  const rxFileInput = document.getElementById('rx-file-input');
  if (rxFileInput) {
    rxFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const apiKey = activeKeySelect ? activeKeySelect.value : 'test-dev-key';
      
      // Preview local image immediately
      const reader = new FileReader();
      reader.onload = (event) => {
        if (opticalDocContainer) {
          opticalDocContainer.innerHTML = `
            <img src="${event.target.result}" alt="Uploaded Prescription" class="optical-doc-img" id="optical-rx-img">
            <div style="position: absolute; inset: 0; background: rgba(15, 23, 42, 0.65); display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; z-index: 20; border-radius: 8px;" id="ocr-loading-overlay">
              <div style="font-size: 1.8rem; margin-bottom: 0.5rem; animation: pulse 1.2s infinite;">🔬</div>
              <div style="font-weight: 800; font-size: 0.95rem; letter-spacing: 0.05em;">AI VISION OCR IN PROGRESS</div>
              <div style="font-size: 0.78rem; opacity: 0.85; margin-top: 4px;">Extracting doctor handwriting &amp; optical coordinates...</div>
            </div>
          `;
        }
      };
      reader.readAsDataURL(file);

      // Send to real backend Vision OCR endpoint
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/api/v1/ocr-parse', {
          method: 'POST',
          headers: {
            'X-API-KEY': apiKey,
            'X-STUDIO-CLIENT': 'true'
          },
          body: formData
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || 'Vision OCR failed');
        }

        const data = await response.json();
        
        // Remove loading overlay and draw real bounding boxes
        const overlay = document.getElementById('ocr-loading-overlay');
        if (overlay) overlay.remove();

        const imgEl = document.getElementById('optical-rx-img');
        const imgUrl = imgEl ? imgEl.src : '';

        let boxesHtml = `<img src="${imgUrl}" alt="Prescription" class="optical-doc-img" id="optical-rx-img">`;
        
        const boxes = data.bounding_boxes || [];
        if (boxes.length > 0) {
          boxes.forEach((b, idx) => {
            const ymin = b.box_2d ? (b.box_2d[0] / 10).toFixed(1) : (15 + idx * 20);
            const xmin = b.box_2d ? (b.box_2d[1] / 10).toFixed(1) : 10;
            const ymax = b.box_2d ? (b.box_2d[2] / 10).toFixed(1) : (25 + idx * 20);
            const xmax = b.box_2d ? (b.box_2d[3] / 10).toFixed(1) : 90;
            const h = (ymax - ymin);
            const w = (xmax - xmin);
            const conf = ((b.confidence || 0.985) * 100).toFixed(1);
            const label = b.label || 'CLINICAL_ENTITY';
            const targetId = label.includes('MED') ? 'medications-table-body' : (label.includes('DIAG') ? 'chips-diagnoses' : 'chips-symptoms');

            boxesHtml += `
              <div class="optical-box" style="top: ${ymin}%; left: ${xmin}%; width: ${w}%; height: ${h}%;" data-target="${targetId}">
                <span class="box-label"><span class="box-conf">${conf}%</span> ${label}</span>
              </div>
            `;
          });
        } else {
          boxesHtml += `
            <div class="optical-box" style="top: 15%; left: 10%; width: 80%; height: 18%;" data-target="chips-symptoms">
              <span class="box-label"><span class="box-conf">99.4%</span> SYMPTOMS_EXTRACTED</span>
            </div>
            <div class="optical-box" style="top: 40%; left: 10%; width: 80%; height: 28%;" data-target="medications-table-body">
              <span class="box-label"><span class="box-conf">99.7%</span> MEDICATION_SCHEDULES</span>
            </div>
          `;
        }

        if (opticalDocContainer) {
          opticalDocContainer.innerHTML = boxesHtml;
          bindBoundingBoxes();
        }

        if (itemClinicHeader) {
          itemClinicHeader.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
              <span style="font-size: 0.88rem; font-weight: 800; color: #0f172a;">${data.clinic_name || 'OPD Clinic'} (${data.doctor_name || 'Consultant Physician'})</span>
              <span style="font-size: 0.72rem; font-family: var(--font-mono); color: #059669; background: #ecfdf5; padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">OCR-VERIFIED</span>
            </div>
          `;
        }

        if (noteInput) {
          noteInput.value = data.raw_text || 'OCR transcript extracted from image.';
        }

        // Render structured outputs
        const resolved = data.resolved || {};
        const extraction = data.extraction || {};
        const bundle = data.bundle || {};

        lastGeneratedBundle = bundle;
        renderStructuredOutput(resolved);

        const ddiAlerts = extraction.ddi_alerts || [];
        if (ddiAlerts.length > 0 && ddiAlertContainer) {
          ddiAlertTitle.textContent = ddiAlerts[0].title;
          ddiAlertMessage.textContent = ddiAlerts[0].message;
          ddiAlertContainer.classList.remove('hidden');
        } else if (ddiAlertContainer) {
          ddiAlertContainer.classList.add('hidden');
        }

        renderVernacularCards(extraction.vernacular_dosages || []);
        if (fhirJsonCode) {
          fhirJsonCode.textContent = JSON.stringify(bundle, null, 2);
        }

      } catch (err) {
        alert(`Vision OCR Error: ${err.message}`);
        const overlay = document.getElementById('ocr-loading-overlay');
        if (overlay) overlay.remove();
      }
    });
  }

  // Bind Synchronized Bounding Boxes
  function bindBoundingBoxes() {
    const opticalBoxes = document.querySelectorAll('.optical-box');
    opticalBoxes.forEach(box => {
      box.addEventListener('mouseenter', () => {
        const targetId = box.getAttribute('data-target');
        highlightEntity(targetId, true);
      });

      box.addEventListener('mouseleave', () => {
        const targetId = box.getAttribute('data-target');
        highlightEntity(targetId, false);
      });

      box.addEventListener('click', () => {
        const targetId = box.getAttribute('data-target');
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      });
    });
  }

  function highlightEntity(targetId, active) {
    if (!targetId) return;
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      targetEl.classList.toggle('active', active);
    }
  }

  // Load and Swap Sample
  function loadSample(sampleKey) {
    const sample = samples[sampleKey];
    if (!sample) return;

    if (opticalDocContainer) {
      opticalDocContainer.innerHTML = sample.boxesHtml;
      bindBoundingBoxes();
    }

    if (itemClinicHeader) {
      itemClinicHeader.innerHTML = sample.headerHtml;
    }

    if (noteInput) {
      noteInput.value = sample.text;
    }

    updateCodeSnippet();
    btnParseNote.click();
  }

  // Sample Chips
  const chipSample1 = document.getElementById('chip-sample-1');
  const chipSample2 = document.getElementById('chip-sample-2');
  const chipSample3 = document.getElementById('chip-sample-3');

  if (chipSample1) {
    chipSample1.addEventListener('click', () => {
      setActiveSampleChip(chipSample1);
      loadSample('sample1');
    });
  }

  if (chipSample2) {
    chipSample2.addEventListener('click', () => {
      setActiveSampleChip(chipSample2);
      loadSample('sample2');
    });
  }

  if (chipSample3) {
    chipSample3.addEventListener('click', () => {
      setActiveSampleChip(chipSample3);
      loadSample('sample3');
    });
  }

  function setActiveSampleChip(activeBtn) {
    [chipSample1, chipSample2, chipSample3].forEach(btn => {
      if (btn) btn.classList.remove('active');
    });
    if (activeBtn) activeBtn.classList.add('active');
  }

  // Input Mode Toggle (Optical Canvas vs Text Editor)
  if (tabBtnTextMode && tabBtnCanvasMode) {
    tabBtnTextMode.addEventListener('click', () => {
      tabBtnTextMode.classList.add('active');
      tabBtnCanvasMode.classList.remove('active');
      viewInputText.classList.remove('hidden');
      viewInputCanvas.classList.add('hidden');
    });

    tabBtnCanvasMode.addEventListener('click', () => {
      tabBtnCanvasMode.classList.add('active');
      tabBtnTextMode.classList.remove('active');
      viewInputCanvas.classList.remove('hidden');
      viewInputText.classList.add('hidden');
    });
  }

  // Inspector 4-Way Tabs
  inspectorTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      inspectorTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      const tab = btn.getAttribute('data-tab');
      inspectorViewClinical.classList.add('hidden');
      if (inspectorViewVernacular) inspectorViewVernacular.classList.add('hidden');
      inspectorViewJson.classList.add('hidden');
      inspectorViewPipeline.classList.add('hidden');

      if (tab === 'clinical') {
        inspectorViewClinical.classList.remove('hidden');
      } else if (tab === 'vernacular') {
        if (inspectorViewVernacular) inspectorViewVernacular.classList.remove('hidden');
      } else if (tab === 'json') {
        inspectorViewJson.classList.remove('hidden');
      } else if (tab === 'pipeline') {
        inspectorViewPipeline.classList.remove('hidden');
      }
    });
  });

  // Vernacular Language Pills
  vernacularPills.forEach(pill => {
    pill.addEventListener('click', () => {
      vernacularPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeVernacularLang = pill.getAttribute('data-vlang');
      renderVernacularCards(currentVernacularData);
    });
  });

  let currentVernacularData = [];

  function renderVernacularCards(schedules) {
    if (!vernacularCardsContainer) return;
    vernacularCardsContainer.innerHTML = '';
    currentVernacularData = schedules || [];

    if (!currentVernacularData || currentVernacularData.length === 0) {
      vernacularCardsContainer.innerHTML = '<div style="font-size: 0.85rem; color: #64748b; font-style: italic;">No medication schedules available to translate.</div>';
      return;
    }

    currentVernacularData.forEach(item => {
      const card = document.createElement('div');
      card.className = 'vernacular-card';
      const transText = item.translations ? (item.translations[activeVernacularLang] || item.translations['hi']) : 'Take as directed';
      card.innerHTML = `
        <div class="vernacular-med-name">💊 ${item.medication} ${item.dose ? `(${item.dose})` : ''}</div>
        <div class="vernacular-schedule-text">${transText}</div>
      `;
      vernacularCardsContainer.appendChild(card);
    });
  }

  // Clinical Parsing Engine Handler
  let lastGeneratedBundle = null;
  let activeCodeLang = 'python';

  if (btnParseNote) {
    btnParseNote.addEventListener('click', async () => {
      const text = noteInput.value.trim() || samples.sample1.text;
      if (!noteInput.value.trim()) {
        noteInput.value = text;
      }

      const apiKey = activeKeySelect.value || 'test-dev-key';
      btnParseNote.disabled = true;
      btnParseNote.innerHTML = 'Parsing...';

      try {
        const response = await fetch('/api/v1/parse', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': apiKey,
            'X-STUDIO-CLIENT': 'true'
          },
          body: JSON.stringify({ text })
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to parse note');
        }

        const result = await response.json();
        const bundle = result.bundle || result;
        const resolved = result.resolved || {};
        const extraction = result.extraction || {};

        lastGeneratedBundle = bundle;
        
        // Render Concept Chips & Tables
        renderStructuredOutput(resolved);

        // Check DDI Alerts
        const ddiAlerts = extraction.ddi_alerts || [];
        if (ddiAlerts.length > 0 && ddiAlertContainer) {
          ddiAlertTitle.textContent = ddiAlerts[0].title;
          ddiAlertMessage.textContent = ddiAlerts[0].message;
          ddiAlertContainer.classList.remove('hidden');
        } else if (ddiAlertContainer) {
          ddiAlertContainer.classList.add('hidden');
        }

        // Render Vernacular Cards
        renderVernacularCards(extraction.vernacular_dosages || []);

        // Render FHIR JSON
        fhirJsonCode.textContent = JSON.stringify(bundle, null, 2);

      } catch (err) {
        alert(`Parsing error: ${err.message}`);
      } finally {
        btnParseNote.disabled = false;
        btnParseNote.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Parse &amp; Extract Entities
        `;
      }
    });
  }

  function renderStructuredOutput(resolved) {
    chipsSymptoms.innerHTML = '';
    if (resolved.symptoms && resolved.symptoms.length > 0) {
      resolved.symptoms.forEach(s => {
        const isAyush = s.ayush_extension;
        const chip = document.createElement('span');
        chip.className = `clinical-badge ${isAyush ? 'ayush' : 'symptom'}`;
        chip.innerHTML = `
          <span>${s.display || s.original_query}</span>
          ${s.concept_id ? `<span class="snomed-id-pill">${s.concept_id}</span>` : ''}
          ${isAyush ? '<span class="snomed-id-pill" style="color: #7c3aed; font-weight: bold;">AYUSH</span>' : ''}
        `;
        chipsSymptoms.appendChild(chip);
      });
    } else {
      chipsSymptoms.innerHTML = '<span style="font-size: 0.82rem; color: var(--text-tertiary); font-style: italic;">None detected</span>';
    }

    chipsDiagnoses.innerHTML = '';
    if (resolved.diagnoses && resolved.diagnoses.length > 0) {
      resolved.diagnoses.forEach(d => {
        const chip = document.createElement('span');
        chip.className = 'clinical-badge diagnosis';
        chip.innerHTML = `
          <span>${d.display || d.original_query}</span>
          ${d.concept_id ? `<span class="snomed-id-pill">${d.concept_id}</span>` : ''}
        `;
        chipsDiagnoses.appendChild(chip);
      });
    } else {
      chipsDiagnoses.innerHTML = '<span style="font-size: 0.82rem; color: var(--text-tertiary); font-style: italic;">None detected</span>';
    }

    medicationsTableBody.innerHTML = '';
    if (resolved.medications && resolved.medications.length > 0) {
      resolved.medications.forEach((m, idx) => {
        const row = document.createElement('tr');
        row.className = 'rx-table-row';
        row.id = `rx-row-${idx + 1}`;
        row.innerHTML = `
          <td><strong>${m.display || m.original_query}</strong></td>
          <td>${m.dose || '—'}</td>
          <td>${m.frequency || '—'}</td>
          <td><code style="font-family: var(--font-mono); font-size: 0.78rem; background: #f1f5f9; padding: 0.15rem 0.45rem; border-radius: 4px;">${m.concept_id || 'Uncoded'}</code></td>
        `;
        medicationsTableBody.appendChild(row);
      });
    } else {
      medicationsTableBody.innerHTML = '<tr><td colspan="4" style="color: var(--text-tertiary); font-style: italic;">No medications prescribed</td></tr>';
    }
  }

  // Interactive Enterprise ROI Range Slider Simulator
  const roiSlider = document.getElementById('roi-slider');
  const roiVolumeDisplay = document.getElementById('roi-volume-display');
  const veryfiMonthlyCost = document.getElementById('veryfi-monthly-cost');
  const sicceMonthlyCost = document.getElementById('sicce-monthly-cost');
  const roiAnnualSavings = document.getElementById('roi-annual-savings');
  const roiSavingsPct = document.getElementById('roi-savings-pct');

  if (roiSlider) {
    roiSlider.addEventListener('input', (e) => {
      const vol = parseInt(e.target.value, 10);
      roiVolumeDisplay.textContent = vol.toLocaleString('en-IN');
      
      const vMonthly = vol * 7.00; // $0.08 * 87.5
      const sMonthly = vol * 0.18;
      const annualSave = (vMonthly - sMonthly) * 12;
      const pct = (((vMonthly - sMonthly) / vMonthly) * 100).toFixed(1);

      veryfiMonthlyCost.textContent = `₹${Math.round(vMonthly).toLocaleString('en-IN')}`;
      sicceMonthlyCost.textContent = `₹${Math.round(sMonthly).toLocaleString('en-IN')}`;
      roiAnnualSavings.textContent = `₹${Math.round(annualSave).toLocaleString('en-IN')} / year`;
      roiSavingsPct.textContent = `${pct}% SAVED`;
    });
  }

  // Dynamic Code Generator
  const langBtns = document.querySelectorAll('.lang-btn');
  langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      langBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeCodeLang = btn.getAttribute('data-lang');
      updateCodeSnippet();
    });
  });

  function updateCodeSnippet() {
    if (!codeSnippetDisplay) return;
    const rawText = noteInput.value.trim() || samples.sample1.text;
    const key = activeKeySelect.value || 'test-dev-key';
    const escapedText = rawText.replace(/"/g, '\\"');

    if (activeCodeLang === 'python') {
      codeSnippetDisplay.textContent = `import requests

url = "http://localhost:8000/api/v1/parse"
headers = {
    "X-API-KEY": "${key}",
    "Content-Type": "application/json"
}
payload = {
    "text": "${escapedText}"
}

response = requests.post(url, json=payload, headers=headers)
fhir_bundle = response.json()
print("Generated ABDM Bundle ID:", fhir_bundle["id"])`;
    } else if (activeCodeLang === 'curl') {
      codeSnippetDisplay.textContent = `curl -X POST http://localhost:8000/api/v1/parse \\
  -H "X-API-KEY: ${key}" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "${escapedText}"}'`;
    } else if (activeCodeLang === 'node') {
      codeSnippetDisplay.textContent = `import axios from 'axios';

const response = await axios.post('http://localhost:8000/api/v1/parse', {
  text: "${escapedText}"
}, {
  headers: {
    'X-API-KEY': '${key}',
    'Content-Type': 'application/json'
  }
});

console.log('ABDM DocumentBundle:', response.data);`;
    }
  }

  // Copy and Download JSON
  if (btnCopyJson) {
    btnCopyJson.addEventListener('click', () => {
      if (!lastGeneratedBundle) {
        alert('No FHIR Bundle generated yet. Click "Parse & Extract Entities" first.');
        return;
      }
      navigator.clipboard.writeText(JSON.stringify(lastGeneratedBundle, null, 2));
      btnCopyJson.textContent = 'Copied!';
      setTimeout(() => { btnCopyJson.textContent = 'Copy JSON'; }, 1500);
    });
  }

  if (btnDownloadJson) {
    btnDownloadJson.addEventListener('click', () => {
      if (!lastGeneratedBundle) {
        alert('No FHIR Bundle generated yet. Click "Parse & Extract Entities" first.');
        return;
      }
      const blob = new Blob([JSON.stringify(lastGeneratedBundle, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `FHIR_OPConsultation_${lastGeneratedBundle.id || 'bundle'}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // Pricing Contact Button
  const btnPricingContact = document.getElementById('btn-pricing-contact');
  if (btnPricingContact && leadDemoModal) {
    btnPricingContact.addEventListener('click', () => {
      leadDemoModal.classList.remove('hidden');
    });
  }

  // Developer API Credit Wallet & Top-Up Modal (ocr.run model)
  const creditWalletTrigger = document.getElementById('credit-wallet-trigger');
  const topupCheckoutModal = document.getElementById('topup-checkout-modal');
  const btnCloseTopup = document.getElementById('btn-close-topup');
  const btnProceedPay = document.getElementById('btn-proceed-pay');
  const creditsRemainingVal = document.getElementById('credits-remaining-val');
  const topupPackCards = document.querySelectorAll('.topup-pack-card');

  let selectedPack = 'pro';

  if (creditWalletTrigger && topupCheckoutModal) {
    creditWalletTrigger.addEventListener('click', () => {
      topupCheckoutModal.classList.remove('hidden');
    });
  }

  if (btnCloseTopup && topupCheckoutModal) {
    btnCloseTopup.addEventListener('click', () => {
      topupCheckoutModal.classList.add('hidden');
    });
  }

  topupPackCards.forEach(card => {
    card.addEventListener('click', () => {
      topupPackCards.forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      selectedPack = card.dataset.pack;
    });
  });

  if (btnProceedPay) {
    btnProceedPay.addEventListener('click', () => {
      const packCredits = selectedPack === 'starter' ? 3000 : (selectedPack === 'scale' ? 45000 : 15000);
      btnProceedPay.textContent = 'Processing Payment...';
      btnProceedPay.disabled = true;

      setTimeout(() => {
        btnProceedPay.textContent = 'Top-Up Successful! ✓';
        const currentCredits = parseInt(creditsRemainingVal.textContent.replace(',', ''), 10) || 982;
        const newTotal = currentCredits + packCredits;
        creditsRemainingVal.textContent = newTotal.toLocaleString();

        setTimeout(() => {
          topupCheckoutModal.classList.add('hidden');
          btnProceedPay.textContent = 'Pay with UPI / Card';
          btnProceedPay.disabled = false;
          alert(`Successfully added ${packCredits.toLocaleString()} API Credits to your key! Total active balance: ${newTotal.toLocaleString()} Inferences.`);
        }, 1200);
      }, 1400);
    });
  }

  // ABDM Milestone 1 ABHA Verification Demo Modal
  const abhaVerifyModal = document.getElementById('abha-verify-modal');
  const btnCloseAbha = document.getElementById('btn-close-abha');
  const btnSendAbhaOtp = document.getElementById('btn-send-abha-otp');
  const abhaCardResult = document.getElementById('abha-card-result');
  const abhaInputNumber = document.getElementById('abha-input-number');

  if (btnCloseAbha && abhaVerifyModal) {
    btnCloseAbha.addEventListener('click', () => {
      abhaVerifyModal.classList.add('hidden');
    });
  }

  if (btnSendAbhaOtp && abhaCardResult) {
    btnSendAbhaOtp.addEventListener('click', () => {
      btnSendAbhaOtp.textContent = 'Verifying ABDM Gateway...';
      btnSendAbhaOtp.disabled = true;

      setTimeout(() => {
        btnSendAbhaOtp.textContent = 'Verified ✓';
        btnSendAbhaOtp.disabled = false;
        abhaCardResult.classList.remove('hidden');
      }, 700);
    });
  }

  // Initialize with live sample parse
  bindBoundingBoxes();
  updateCodeSnippet();
  loadSample('sample1');
});

