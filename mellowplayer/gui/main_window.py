import logging
from PyQt4 import QtCore, QtGui
from mellowplayer import __version__, system
from mellowplayer.api import ServiceManager, SongStatus
from .dlg_select_service import DlgSelectService
from .forms.main_window_ui import Ui_MainWindow
from mellowplayer.api.mpris2 import Mpris2
from mellowplayer.settings import Settings


def _logger():
    return logging.getLogger(__name__)


class MainWindow(QtGui.QMainWindow):
    song_changed = QtCore.pyqtSignal(object)
    playback_status_changed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.services = ServiceManager(self.ui.webView)
        self.setWindowTitle('MellowPlayer %s' % __version__)
        self.ui.pushButtonSelect.setFocus()
        self._start_current()
        self.ui.pushButtonQuit.clicked.connect(self.close)
        self.ui.actionQuit.triggered.connect(self.close)
        self._init_tray_icon()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_song_status)
        self.timer.start(10)
        self._current_song = None
        self._prev_status = None
        self.mpris = Mpris2(self)

    #--- Update song status and infos
    def _update_song_status(self):
        _logger().debug('updating sound status')
        song = self.services.current_song
        if song != self._current_song:
            self._current_song = song
            self._notify_new_song()
        if song:
            status = song.status
        else:
            status = SongStatus.Stopped
        if status != self._prev_status:
            self.playback_status_changed.emit(SongStatus.to_string(status))
            self._prev_status = status
        if song:
            self.setWindowTitle(
                '%s - MellowPlayer' % str(song))
            self.tray_icon.setToolTip(
                '%s - MellowPlayer' % song.pretty_string())
            self.action_current_song.setText(str(song))
            self.action_current_song.setEnabled(True)
            self.ui.actionNext.setEnabled(True)
            self.ui.actionPrevious.setEnabled(True)
            if song.status <= SongStatus.Playing:
                self.action_current_song.setIcon(self.ui.actionPlay.icon())
                self.ui.actionPlay.setEnabled(False)
                self.ui.actionPause.setEnabled(True)
                self.ui.actionStop.setEnabled(True)
            elif song.status == SongStatus.Paused:
                self.action_current_song.setIcon(self.ui.actionPause.icon())
                self.ui.actionPlay.setEnabled(True)
                self.ui.actionPause.setEnabled(False)
                self.ui.actionStop.setEnabled(True)
            elif song.status == SongStatus.Stopped:
                self.action_current_song.setIcon(self.ui.actionStop.icon())
                self.ui.actionPlay.setEnabled(False)
                self.ui.actionPause.setEnabled(False)
                self.ui.actionStop.setEnabled(False)
        else:
            self.setWindowTitle('MellowPlayer')
            self.tray_icon.setToolTip('MellowPlayer')
            self.action_current_song.setIcon(self.ui.actionStop.icon())
            self.action_current_song.setEnabled(False)
            self.action_current_song.setText('No song selected')
            self.ui.actionNext.setEnabled(False)
            self.ui.actionPrevious.setEnabled(False)
            self.ui.actionPlay.setEnabled(False)
            self.ui.actionPause.setEnabled(False)
            self.ui.actionStop.setEnabled(False)

    #--- system tray icon and close logic
    def close(self):
        super().close()
        self.mpris.setParent(None)
        self.mpris.destroy()
        self.mpris = None

    def closeEvent(self, ev=None):
        hide = ev is not None and self.isVisible()
        hide &= ((self._current_song is not None and
                  self._current_song.status <= SongStatus.Playing) or
                 not Settings().exit_on_close_if_not_playing)
        if hide:
            if not Settings().flg_close:
                QtGui.QMessageBox.information(
                    self, 'Mellow Player',
                    'The program will keep running in the '
                    'system tray. To terminate the program, '
                    'choose <b>Quit</b> in the context menu '
                    'of the system tray entry.')
                Settings().flg_close = True
            self.hide()
            ev.ignore()

    def _init_tray_icon(self):
        self.tray_icon = QtGui.QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())
        menu = QtGui.QMenu(self)
        action_restore = QtGui.QAction('Restore window', self)
        action_restore.triggered.connect(self.show)
        action_restore.setIcon(QtGui.QIcon.fromTheme(
            'Restore', QtGui.QIcon(':/view-restore.svg')))
        menu.addAction(action_restore)
        self.action_restore = action_restore
        menu.addSeparator()
        self.action_current_song = QtGui.QAction('No song', self)
        self.action_current_song.setEnabled(False)
        menu.addAction(self.action_current_song)
        menu.addSeparator()
        menu.addActions(self.ui.menuPlayback.actions())
        menu.addSeparator()
        menu.addActions(self.ui.menuApplication.actions())
        self.ui.menuPlayback.insertAction(
            self.ui.actionPlay, self.action_current_song)
        self.ui.menuPlayback.insertSeparator(self.ui.actionPlay)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self._on_tray_icon_activated)

    def _on_tray_icon_activated(self, reason):
        if reason in (QtGui.QSystemTrayIcon.Trigger,
                      QtGui.QSystemTrayIcon.DoubleClick):
            self.show()

    def setVisible(self, visible):
        super().setVisible(visible)
        if Settings().always_show_tray_icon:
            self.tray_icon.show()
        else:
            # only show tray if the window is not visible
            self.tray_icon.setVisible(not visible)
        self.action_restore.setEnabled(not visible)

    #--- slots
    @QtCore.pyqtSlot()
    def on_pushButtonSelect_clicked(self):
        self._select_service()

    @QtCore.pyqtSlot()
    def on_actionSelect_service_triggered(self):
        self._select_service()

    @QtCore.pyqtSlot()
    def on_actionReport_a_bug_triggered(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromEncoded(
            'https://github.com/ColinDuquesnoy/MellowPlayer/issues/new?tit'
            'le=Issue%3A &body=%23%23%23%20Description%20of%20the%20issue%0A%'
            '0A%0A%23%23%23%20System%20information%0A*%20Operating%20System%3A'
            '%20%0A*%20Mellow%20Player%20Version%3A%0A*%20Service%3A%0A*%20'
            'Service%20version'))

    @QtCore.pyqtSlot()
    def on_actionPlay_triggered(self):
        self.services.play()

    @QtCore.pyqtSlot()
    def on_actionPause_triggered(self):
        self.services.pause()

    @QtCore.pyqtSlot()
    def on_actionStop_triggered(self):
        self.services.stop()

    @QtCore.pyqtSlot()
    def on_actionNext_triggered(self):
        self.services.next()

    @QtCore.pyqtSlot()
    def on_actionPrevious_triggered(self):
        self.services.previous()

    #--- internal helper methods
    def _start_current(self):
        if self.services.start_current_service():
            self.ui.stackedWidget.setCurrentIndex(1)
        else:
            self.ui.stackedWidget.setCurrentIndex(0)

    def _select_service(self):
        self.show()
        service = DlgSelectService.select_service(self)
        if service and service != self.services.current_service:
            self.services.current_service = service
            self._start_current()

    def _notify_new_song(self):
        _logger().info('new song: %s' % self._current_song)
        self.song_changed.emit(self._current_song)