document.addEventListener('DOMContentLoaded', () => {
  const defaultErrorMessage = 'Server error, please try again later.';
  let hoverTimer = null;

  function handleFetchError(error) {
    console.error('Fetch error:', error);
    let message = defaultErrorMessage;
    if (error.response && error.response.hasOwnProperty('message')) {
      message = error.response.message;
    }
    toast(message, 'error');
  }

  function toast(message, category) {
    const toastElem = document.getElementById('mainToast');
    const toast = bootstrap.Toast.getOrCreateInstance(toastElem);
    toastElem.querySelector('.toast-body').textContent = message;

    if (category === 'error') {
      toastElem.classList.replace('text-bg-secondary', 'text-bg-danger');
    } else {
      toastElem.classList.replace('text-bg-danger', 'text-bg-secondary');
    }
    toast.show();
  }

  function showProfilePopover(event) {
    const elem = event.target;

    hoverTimer = setTimeout(() => {
      hoverTimer = null;
      fetch(elem.dataset.href)
        .then(response => response.text())
        .then(data => {
          const popover = bootstrap.Popover.getOrCreateInstance(elem, {
              content: data,
              html: true,
              sanitize: false,
              trigger: 'manual',
            });
          popover.setContent({
            '.popover-body': data
          })
          popover.show();
          document.querySelector('.popover').addEventListener('mouseleave', () => {
            setTimeout(() => {
              popover.hide();
            }, 200);
          });
        })
        .catch(handleFetchError);
    }, 500);
  }

  function hideProfilePopover(event) {
    const elem = event.target;

    if (hoverTimer) {
      clearTimeout(hoverTimer);
      hoverTimer = null;
    } else {
      setTimeout(() => {
        if (!document.querySelector('.popover:hover')) {
          const popover = bootstrap.Popover.getInstance(elem);
          popover.hide();
        }
      }, 200);
    }
  }

  document.querySelectorAll('.profile-popover').forEach(elem => {
    elem.addEventListener('mouseenter', showProfilePopover);
    elem.addEventListener('mouseleave', hideProfilePopover);
  });


  function updateFollowersCount(id) {
    const elem = document.getElementById('followers-count-' + id);
    fetch(elem.dataset.href)
      .then(response => response.json())
      .then(data => {
        elem.textContent = data.count;
      })
      .catch(handleFetchError);
  }

  function updateCollectorsCount(id) {
    const elem = document.getElementById('collectors-count-' + id);
    fetch(elem.dataset.href)
      .then(response => response.json())
      .then(data => {
        elem.textContent = data.count;
      })
      .catch(handleFetchError);
  }

  function updateNotificationsCount() {
    const elem = document.getElementById('notification-badge');
    if (!elem) {
      return;
    }
    fetch(elem.dataset.href)
      .then(response => response.json())
      .then(data => {
        if (data.count === 0) {
          elem.style.display = 'none';
        } else {
          elem.style.display = 'block';
          elem.textContent = data.count;
        }
      })
      .catch(handleFetchError);
  }

  function follow(event) {
    const elem = event.target;
    const id = elem.dataset.id;
    fetch(elem.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      }
    })
      .then(response => response.json())
      .then(data => {
        elem.previousElementSibling.style.display = 'inline-block';
        elem.style.display = 'none';
        updateFollowersCount(id);
        toast(data.message);
      })
      .catch(handleFetchError);
  }

  function unfollow(event) {
    const elem = event.target;
    const id = elem.dataset.id;
    fetch(elem.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      }
    })
      .then(response => response.json())
      .then(data => {
        elem.nextElementSibling.style.display = 'inline-block';
        elem.style.display = 'none';
        updateFollowersCount(id);
        toast(data.message);
      })
      .catch(handleFetchError);
  }

  function collect(event) {
    let elem = event.target;
    while (elem && !elem.classList.contains('collect-btn')) {
      elem = elem.parentElement;
    }
    const id = elem.dataset.id;
    fetch(elem.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      }
    })
      .then(response => response.json())
      .then(data => {
        elem.previousElementSibling.style.display = 'block';
        elem.style.display = 'none';
        updateCollectorsCount(id);
        toast(data.message);
      })
      .catch(handleFetchError);
  }

  function uncollect(event) {
    let elem = event.target;
    while (elem && !elem.classList.contains('uncollect-btn')) {
      elem = elem.parentElement;
    }
    const id = elem.dataset.id;
    fetch(elem.dataset.href, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      }
    })
      .then(response => response.json())
      .then(data => {
        elem.nextElementSibling.style.display = 'block';
        elem.style.display = 'none';
        updateCollectorsCount(id);
        toast(data.message);
      })
      .catch(handleFetchError);
  }

  dayjs.extend(window.dayjs_plugin_relativeTime)
  dayjs.extend(window.dayjs_plugin_utc)
  dayjs.extend(window.dayjs_plugin_localizedFormat)

  function renderAllDatetime() {
    // render normal time
    const elements = document.querySelectorAll('.dayjs');
    elements.forEach(elem => {
      const date = dayjs.utc(elem.innerHTML);
      const format = elem.dataset.format ?? 'LL';
      elem.innerHTML = date.local().format(format);
    });
    // render from now time
    const fromNowElements = document.querySelectorAll('.dayjs-from-now');
    fromNowElements.forEach(elem => {
      const date = dayjs.utc(elem.innerHTML);
      elem.innerHTML = date.local().fromNow();
    });
    // render tooltip time
    const toolTipElements = document.querySelectorAll('.dayjs-tooltip');
    toolTipElements.forEach(elem => {
      const date = dayjs.utc(elem.dataset.timestamp);
      const format = elem.dataset.format ?? 'LLL';
      elem.dataset.bsTitle = date.local().format(format);
      const tooltip = new bootstrap.Tooltip(elem);
    });
  }

  document.addEventListener('click', event => {
    if (event.target.classList.contains('follow-btn')) {
      follow(event);
    } else if (event.target.classList.contains('unfollow-btn')) {
      unfollow(event);
    }
  });

  if (document.getElementsByClassName('collect-btn')) {
    document.querySelectorAll('.collect-btn').forEach(elem => {
      elem.addEventListener('click', collect);
    });
  }

  if (document.getElementsByClassName('uncollect-btn')) {
    document.querySelectorAll('.uncollect-btn').forEach(elem => {
      elem.addEventListener('click', uncollect);
    });
  }

  if (document.getElementById('tag-btn')) {
    document.getElementById('tag-btn').addEventListener('click', () => {
      document.getElementById('tags').style.display = 'none';
      document.getElementById('tag-form').style.display = 'block';
    });
  }

  if (document.getElementById('cancel-tag')) {
    document.getElementById('cancel-tag').addEventListener('click', () => {
      document.getElementById('tag-form').style.display = 'none';
      document.getElementById('tags').style.display = 'block';
    });
  }

  const descriptionBtn = document.getElementById('description-btn');
  const cancelDescription = document.getElementById('cancel-description');
  const description = document.getElementById('description');
  const descriptionForm = document.getElementById('description-form');

  if (descriptionBtn) {
    descriptionBtn.addEventListener('click', () => {
      description.style.display = 'none';
      descriptionForm.style.display = 'block';
    });
  }

  if (cancelDescription) {
    cancelDescription.addEventListener('click', () => {
      descriptionForm.style.display = 'none';
      description.style.display = 'block';
    });
  }

  const deleteModal = document.getElementById('delete-modal');
  const deleteForm = document.querySelector('.delete-form');

  if (deleteModal && deleteForm) {
    deleteModal.addEventListener('show.bs.modal', event => {
      deleteForm.setAttribute('action', event.relatedTarget.dataset.href);
    });
  }

  if (isAuthenticated) {
    setInterval(updateNotificationsCount, 30000);
  }

  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(tooltipTriggerElem => {
    return new bootstrap.Tooltip(tooltipTriggerElem);
  });

  renderAllDatetime();
});
