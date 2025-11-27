import { useEffect, useState } from 'react';
import { Content, InfoCard, Progress } from '@backstage/core-components';
import { Grid, Typography } from '@material-ui/core';

export const DqtimesMonitorPage = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 🚀 Chama o endpoint FastAPI
        const response = await fetch('http://localhost:8000/monitor/status');
        const json = await response.json();
        setData(json);
      } catch (error) {
        console.error('Erro ao buscar dados do monitoramento', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // Atualiza a cada 10 segundos
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return <Progress />;
  }

  const { task_states, redis, workers_total } = data;

  return (
    <Content>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Typography variant="h4">Monitoramento DQTimes</Typography>
        </Grid>

        <Grid item xs={4}>
          <InfoCard title="Tarefas Concluídas" subheader="Celery / Flower">
            <Typography variant="h3" color="primary">
              {task_states.SUCCESS}
            </Typography>
          </InfoCard>
        </Grid>

        <Grid item xs={4}>
          <InfoCard title="Tarefas Pendentes">
            <Typography variant="h3">{task_states.PENDING}</Typography>
          </InfoCard>
        </Grid>

        <Grid item xs={4}>
          <InfoCard title="Tarefas com Falha">
            <Typography variant="h3" color="error">
              {task_states.FAILURE}
            </Typography>
          </InfoCard>
        </Grid>

        <Grid item xs={12}>
          <InfoCard title="Status Geral">
            <Typography>Redis: {redis}</Typography>
            <Typography>Workers ativos: {workers_total}</Typography>
          </InfoCard>
        </Grid>
      </Grid>
    </Content>
  );
};