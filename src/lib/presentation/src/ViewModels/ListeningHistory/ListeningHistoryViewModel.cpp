#include <MellowPlayer/Presentation/ViewModels/ListeningHistory/ListeningHistoryViewModel.hpp>
#include <MellowPlayer/Domain/ListeningHistory/ListeningHistory.hpp>

using namespace MellowPlayer::Domain;
using namespace MellowPlayer::Domain;
using namespace MellowPlayer::Presentation;

ListeningHistoryViewModel::ListeningHistoryViewModel(IListeningHistory &listeningHistory,
                                                     IContextProperties& contextProperties)
        : ContextProperty("_listeningHistory", this, contextProperties),
          listeningHistoryService_(listeningHistory),
          sourceModel_(new QQmlObjectListModel<ListeningHistoryEntryViewModel>(this, "title", "entryId")),
          proxyModel_(sourceModel_)
{
    proxyModel_.setSourceModel(sourceModel_);
}

ListeningHistoryProxyListModel* ListeningHistoryViewModel::model()
{
    return &proxyModel_;
}

void ListeningHistoryViewModel::onEntryAdded(const ListeningHistoryEntry& entry)
{
    sourceModel_->prepend(new ListeningHistoryEntryViewModel(entry, this));
}

void ListeningHistoryViewModel::onEntryRemoved(int entryId)
{
    sourceModel_->remove(sourceModel_->getByUid(QString("%1").arg(entryId)));
}

void ListeningHistoryViewModel::initialize()
{
    connect(&listeningHistoryService_, &ListeningHistory::entryAdded, this, &ListeningHistoryViewModel::onEntryAdded);
    connect(&listeningHistoryService_, &ListeningHistory::entryRemoved, this, &ListeningHistoryViewModel::onEntryRemoved);
    listeningHistoryService_.initialize();
    for (auto entry : listeningHistoryService_.toList())
        onEntryAdded(entry);
}

void ListeningHistoryViewModel::disableService(const QString& serviceName, bool disable)
{
    proxyModel_.disableService(serviceName, disable);
}

void ListeningHistoryViewModel::setSearchFilter(const QString& searchFilter)
{
    proxyModel_.setSearchFilter(searchFilter);
}

void ListeningHistoryViewModel::removeById(int id)
{
    listeningHistoryService_.removeById(id);
}

void ListeningHistoryViewModel::removeByDateCategory(const QString& dateCategory)
{
    QList<int> toRemove;
    for (int i = 0; i < sourceModel_->count(); ++i) {
        ListeningHistoryEntryViewModel* entry = sourceModel_->at(i);
        if (entry->dateCategory() == dateCategory)
            toRemove.append(entry->entryId());
    }
    listeningHistoryService_.removeManyById(toRemove);
}
