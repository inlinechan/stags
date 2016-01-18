;;; stags.el --- query location and display the result from `stags'

;; Copyright (C) 2015 Hyungchan Kim

;; Author: Hyungchan Kim <inlinechan@gmail.com>

;; This file is not part of GNU Emacs.

;; GNU Emacs is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; GNU Emacs is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.

;;; Commentary:

;; This package provides the stags

;;; Code:

(require 'compile)

;; override compilation-last-buffer
(defvar stags-last-buffer nil
  "The most recent stags buffer.
A stags buffer becomes most recent when you select Stags mode in it.
Notice that using \\[next-error] or \\[compile-goto-error] modifies
`compilation-last-buffer' rather than `stags-last-buffer'.")

(defconst stags-symbol-regexp "[A-Za-z_][A-Za-z_0-9]*"
  "Regexp matching tag name.")

(defconst stags-definition-regexp "#[ \t]*define[ \t]+\\|ENTRY(\\|ALTENTRY("
  "Regexp matching tag definition name.")

(defvar stags-rootdir nil
  "Root directory of source tree where stags.db file exist.")

(defvar stags-mode-map
  (let ((map (make-sparse-keymap)))
    (set-keymap-parent map compilation-minor-mode-map)
    (define-key map " " 'scroll-up-command)
    (define-key map "\^?" 'scroll-down-command)
    (define-key map "\C-c\C-f" 'next-error-follow-minor-mode)

    (define-key map "\r" 'compile-goto-error)  ;; ?
    (define-key map "n" 'next-error-no-select)
    (define-key map "p" 'previous-error-no-select)
    (define-key map "{" 'compilation-previous-file)
    (define-key map "}" 'compilation-next-file)
    (define-key map "\t" 'compilation-next-error)
    (define-key map [backtab] 'compilation-previous-error)
    map)
  "Keymap for stags buffers.
`compilation-minor-mode-map' is a cdr of this.")

;; (defvar stags-mode-tool-bar-map nil)

;;;###autoload
(define-compilation-mode stags-mode "stags"
  "Sets `stags-last-buffer' and `compilation-window-height'."
  (setq stags-last-buffer (current-buffer))
  ;; (set (make-local-variable 'tool-bar-map) stags-mode-tool-bar-map)
  ;; (set (make-local-variable 'compilation-error-face)
  ;;      grep-hit-face)
  ;; (set (make-local-variable 'compilation-error-regexp-alist)
  ;;      grep-regexp-alist)
  ;; compilation-directory-matcher can't be nil, so we set it to a regexp that
  ;; can never match.
  ;; (set (make-local-variable 'compilation-directory-matcher) '("\\`a\\`"))
  ;; (set (make-local-variable 'compilation-process-setup-function)
  ;;      'grep-process-setup)
  (set (make-local-variable 'compilation-disable-input) t)
  ;; (set (make-local-variable 'compilation-error-screen-columns)
  ;;      grep-error-screen-columns)
  (add-hook 'compilation-filter-hook 'stags-filter nil t))

(defun stags-match-string (n)
  (buffer-substring (match-beginning n) (match-end n)))

;; from stags.el
(defun stags-current-token ()
  (save-excursion
    (cond
     ((looking-at "[0-9A-Za-z_]")
      (while (and (not (bolp)) (looking-at "[0-9A-Za-z_]"))
        (forward-char -1))
      (if (not (looking-at "[0-9A-Za-z_]")) (forward-char 1)))
     (t
      (while (looking-at "[ \t]")
        (forward-char 1))))
    (if (and (bolp) (looking-at stags-definition-regexp))
        (goto-char (match-end 0)))
    (if (looking-at stags-symbol-regexp)
        (stags-match-string 0) nil)))

(defvar stags-history-list nil
  "stags history list.")

(defun stags-completing-reference ())

(defun stags-get-db-name ()
  (expand-file-name (concat stags-rootdir "/stags.db")))

(defun stags-find-reference ()
  (interactive)
  (stags-query "Reference"))

(defun stags-find-reference-all ()
  (interactive)
  (stags-query "ReferenceInherit"))

(defun stags-goto-declaration ()
  (interactive)
  (stags-query "Declaration"))

(defun stags-goto-definition ()
  (interactive)
  (stags-query "Definition"))

(defun stags-show-symbolinfo ()
  (interactive)
  (stags-query "SymbolInfo"))

(defun stags-class-hierarchy ()
  (interactive)
  (stags-query "ClassHierarchy"))

(defun stags-query (type)
  "Send query `type' to db"
  (when (not stags-rootdir)
    (error "stags-rootdir nil"))
  (let* ((filename (expand-file-name (buffer-file-name)))
         (locus (format "%d:%d" (line-number-at-pos) (1+ (current-column))))
         (locus-fallback)
         (token (stags-current-token))
         (token-fallback)
         (query)
         (status)
         (buffer (generate-new-buffer (generate-new-buffer-name (concat "*STAGS SELECT* " token)))))
    (save-excursion
      (backward-word)
      (setq token-fallback (stags-current-token))
      (setq locus-fallback (format "%d:%d" (line-number-at-pos) (1+ (current-column)))))
    (set-buffer buffer)
    (setq status (call-process "python" nil t nil
                               "-m"
                               "stags.query"
                               (stags-get-db-name)
                               type
                               (concat filename ":" locus)))
    (when (and (string-equal token token-fallback) (not (= status 0)))
      (erase-buffer)
      (message "query failed(%d) try with locus-fallback: %s" status locus-fallback)
      (setq status (call-process "python" nil t nil
                                 "-m"
                                 "stags.query"
                                 (stags-get-db-name)
                                 type
                                 (concat filename ":" locus-fallback))))

    (if (string-equal type "SymbolInfo")
        (progn
          (python-mode)
          (use-local-map (copy-keymap python-mode-map))
          (local-set-key "q" 'kill-this-buffer)
          (read-only-mode t)
          (beginning-of-buffer)
          (switch-to-buffer buffer))
      (if (string-equal type "ClassHierarchy")
          (progn
            (text-mode)
            (clear-image-cache nil)
            (iimage-mode)
            (use-local-map (copy-keymap python-mode-map))
            (local-set-key "q" 'kill-this-buffer)
            (read-only-mode t)
            (switch-to-buffer buffer))
        (let (has-single-candidate )
          (save-excursion
            (let* ((start (point-min))
                   (end (point-max))
                   (nbr-line (count-lines start end)))
              (when (= nbr-line 1)
                (setq has-single-candidate t))))
          (stags-mode)
          (beginning-of-buffer)
          (if has-single-candidate
              (progn
                (beginning-of-buffer)
                (let (filename lineno column new-buffer)
                  (when (looking-at "[^:]+")
                    (setq filename (stags-match-string 0)))
                  (goto-char (match-end 0))
                  (forward-char)
                  (when (looking-at "[^:]+")
                    (setq lineno (stags-match-string 0)))
                  (goto-char (match-end 0))
                  (forward-char)
                  (when (looking-at "[^:]+")
                    (setq column (stags-match-string 0)))
                  (message "%s:%s:%s" filename lineno column)
                  (let ((new-buffer (find-file-noselect filename)))
                    (switch-to-buffer new-buffer)
                    (goto-line (string-to-number lineno))
                    (beginning-of-line)
                    (forward-char (1- (string-to-number column))))
                  (kill-buffer (buffer-name buffer))))
            (switch-to-buffer buffer)))))))

(defun stags-get-rootpath ()
  nil)

(defun stags-visit-rootdir ()
  "Tell the root directory of source tree."
  (interactive)
  (let (path input)
    (setq path stags-rootdir)
    (when (not path)
      (setq path (stags-get-rootpath)))
    (setq input (read-file-name "Visit root directory: " path path t))
    (if (equal "" input) nil
      (if (not (file-directory-p input))
          (message "%s is not directory." input)
        (setq stags-rootdir (expand-file-name input))
        (setenv "STAGSROOT" stags-rootdir)))))

(provide 'stags)

;;; stags.el ends here
