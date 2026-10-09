/**
 * Online Exam Engine Script
 * Handles Countdown Timer, Question Carousel, Question Palette States, Anti-Cheat, and Submission.
 */

document.addEventListener('DOMContentLoaded', function () {
  const examForm = document.getElementById('examForm');
  if (!examForm) return;

  const totalQuestions = parseInt(examForm.dataset.totalQuestions, 10);
  const durationMinutes = parseInt(examForm.dataset.durationMinutes, 10);
  let timeRemaining = durationMinutes * 60;
  let timeSpent = 0;
  let currentQuestionIndex = 1;

  // DOM Elements
  const timerDisplay = document.getElementById('timerDisplay');
  const timeSpentInput = document.getElementById('timeSpentInput');
  const prevBtn = document.getElementById('prevQuestionBtn');
  const nextBtn = document.getElementById('nextQuestionBtn');
  const reviewCheckbox = document.getElementById('markReviewCheckbox');
  const answeredCountEl = document.getElementById('answeredCount');
  const progressBarEl = document.getElementById('examProgressBar');

  // Track review state per question: { [questionNumber]: boolean }
  const reviewStates = {};

  // 1. Timer Logic
  const timerInterval = setInterval(function () {
    if (timeRemaining <= 0) {
      clearInterval(timerInterval);
      alert("Time is up! Your exam will now be submitted automatically.");
      examForm.submit();
      return;
    }

    timeRemaining--;
    timeSpent++;
    if (timeSpentInput) timeSpentInput.value = timeSpent;

    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

    if (timerDisplay) {
      timerDisplay.textContent = formatted;
      if (timeRemaining <= 120) {
        timerDisplay.classList.add('timer-warning');
      }
    }
  }, 1000);

  // 2. Question Navigation Logic
  function showQuestion(qNumber) {
    if (qNumber < 1 || qNumber > totalQuestions) return;

    // Hide all question panes
    document.querySelectorAll('.question-pane').forEach(el => {
      el.classList.add('d-none');
    });

    // Show current question pane
    const targetPane = document.getElementById(`question-pane-${qNumber}`);
    if (targetPane) targetPane.classList.remove('d-none');

    currentQuestionIndex = qNumber;

    // Update Nav Buttons
    if (prevBtn) prevBtn.disabled = (currentQuestionIndex === 1);
    if (nextBtn) {
      if (currentQuestionIndex === totalQuestions) {
        nextBtn.innerHTML = 'Review Answers <i class="fas fa-check-double ms-1"></i>';
      } else {
        nextBtn.innerHTML = 'Next Question <i class="fas fa-arrow-right ms-1"></i>';
      }
    }

    // Sync Mark for Review Checkbox
    if (reviewCheckbox) {
      reviewCheckbox.checked = !!reviewStates[currentQuestionIndex];
    }

    updatePalette();
  }

  // 3. Update Question Palette & Counter
  function updatePalette() {
    let answeredTotal = 0;

    for (let i = 1; i <= totalQuestions; i++) {
      const paletteBtn = document.getElementById(`palette-btn-${i}`);
      if (!paletteBtn) continue;

      // Check if radio option selected
      const isSelected = !!document.querySelector(`input[name="question_${paletteBtn.dataset.questionId}"]:checked`);
      const isMarked = !!reviewStates[i];

      if (isSelected) answeredTotal++;

      // Reset classes
      paletteBtn.className = 'palette-btn btn';

      if (i === currentQuestionIndex) {
        paletteBtn.classList.add('current');
      }

      if (isMarked) {
        paletteBtn.classList.add('btn-warning', 'text-dark');
      } else if (isSelected) {
        paletteBtn.classList.add('btn-success', 'text-white');
      } else {
        paletteBtn.classList.add('btn-outline-secondary');
      }
    }

    if (answeredCountEl) answeredCountEl.textContent = answeredTotal;
    if (progressBarEl) {
      const progressPercent = Math.round((answeredTotal / totalQuestions) * 100);
      progressBarEl.style.width = `${progressPercent}%`;
      progressBarEl.setAttribute('aria-valuenow', progressPercent);
    }
  }

  // Listen to option changes
  document.querySelectorAll('.option-input').forEach(input => {
    input.addEventListener('change', function () {
      updatePalette();
    });
  });

  // Listen to Mark for Review toggle
  if (reviewCheckbox) {
    reviewCheckbox.addEventListener('change', function () {
      reviewStates[currentQuestionIndex] = this.checked;
      updatePalette();
    });
  }

  // Prev / Next button listeners
  if (prevBtn) {
    prevBtn.addEventListener('click', function () {
      if (currentQuestionIndex > 1) {
        showQuestion(currentQuestionIndex - 1);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', function () {
      if (currentQuestionIndex < totalQuestions) {
        showQuestion(currentQuestionIndex + 1);
      } else {
        // Scroll to submit section
        const submitSection = document.getElementById('examSubmitSection');
        if (submitSection) submitSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  // Palette button direct clicks
  document.querySelectorAll('.palette-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const targetIndex = parseInt(this.dataset.index, 10);
      showQuestion(targetIndex);
    });
  });

  // 4. Anti-Cheat: Tab Switch Detection
  let tabSwitchCount = 0;
  window.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      tabSwitchCount++;
      const warningBanner = document.getElementById('antiCheatWarning');
      const warningCountText = document.getElementById('switchWarningCount');

      if (warningBanner) {
        warningBanner.classList.remove('d-none');
        if (warningCountText) warningCountText.textContent = tabSwitchCount;
      }
    }
  });

  // 5. Initialize view
  showQuestion(1);
});
