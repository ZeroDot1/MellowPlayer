#include <MellowPlayer/Presentation/Notifications/Presenters/Linux/LibnotifyPresenter.hpp>
#include <MellowPlayer/Presentation/Notifications/Presenters/Linux/LibnotifyStrings.hpp>
#include <MellowPlayer/Domain/Logging/ILogger.hpp>
#include <MellowPlayer/Domain/Logging/Loggers.hpp>
#include <MellowPlayer/Domain/Logging/LoggingMacros.hpp>
#include <MellowPlayer/Presentation/Notifications/Notification.hpp>
#include <MellowPlayer/Presentation/IMainWindow.hpp>
#undef Q_SIGNALS
#include <libnotify/notify.h>

using namespace std;
using namespace MellowPlayer::Domain;
using namespace MellowPlayer::Domain;
using namespace MellowPlayer::Presentation;

LibnotifyPresenter* LibnotifyPresenter::instance_ = nullptr;

void notify_action_callback(NotifyNotification*, char*, gpointer)
{
    LibnotifyPresenter::onActionCallback();
}

LibnotifyPresenter::LibnotifyPresenter(IMainWindow& mainWindow, IWorkDispatcher& workDispatcher)
        : logger_(Loggers::logger("LibnotifyPresenter")),
          mainWindow_(mainWindow),
          _workDispatcher(workDispatcher),
          previousNotification_(nullptr)
{
    instance_ = this;
}

void LibnotifyPresenter::initialize()
{
    notify_init("MellowPlayer");
    checkSupportForActions();
    LOG_DEBUG(logger_, "service started")
}

void LibnotifyPresenter::checkSupportForActions() {
    GList* caps = notify_get_server_caps();
    if (g_list_find_custom(caps, "actions", (GCompareFunc) g_strcmp0) == NULL)
        actionsSupported_ = false;
    g_list_free_full(caps, g_free);
}

bool LibnotifyPresenter::display(const Notification& notification)
{
    Q_UNUSED(notification)
    static LibnotifyStrings strings;

    if (previousNotification_)
        notify_notification_close(previousNotification_, 0);

    QString title = "MellowPlayer - " + notification.title;
    NotifyNotification* n = notify_notification_new(
            title.toStdString().c_str(),
            notification.description.toStdString().c_str(),
            notification.icon.toStdString().c_str());
    notify_notification_set_timeout(n, 5000);
    string openStr = strings.open();
    if (actionsSupported_)
        notify_notification_add_action(n, "open", strings.open().c_str(),
                                       (NotifyActionCallback)notify_action_callback, nullptr, nullptr);

    _workDispatcher.invoke([=]() {
        notify_notification_show(n, 0);
    });

    previousNotification_ = n;

    return true;
}

void LibnotifyPresenter::onActionCallback()
{
    instance_->mainWindow_.show();
}
