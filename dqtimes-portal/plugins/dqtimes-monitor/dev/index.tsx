import { createDevApp } from '@backstage/dev-utils';
import { dqtimesMonitorPlugin, DqtimesMonitorPage } from '../src/plugin';

createDevApp()
  .registerPlugin(dqtimesMonitorPlugin)
  .addPage({
    element: <DqtimesMonitorPage />,
    title: 'Root Page',
    path: '/dqtimes-monitor',
  })
  .render();
