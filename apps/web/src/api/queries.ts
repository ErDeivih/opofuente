import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  activateOpposition,
  fetchConvocation,
  fetchCurriculum,
  fetchCurriculumNode,
  fetchOppositions,
} from './profiles';
import { fetchCapabilities, fetchReadiness, fetchSettings } from './system';

export const queryKeys = {
  readiness: ['system', 'readiness'] as const,
  capabilities: ['system', 'capabilities'] as const,
  settings: ['system', 'settings'] as const,
  oppositions: ['profiles', 'oppositions'] as const,
  convocation: (id: string) => ['profiles', 'convocation', id] as const,
  curriculum: (id: string) => ['profiles', 'curriculum', id] as const,
  curriculumNode: (id: string) => ['profiles', 'curriculum-node', id] as const,
};

export function useReadiness() {
  return useQuery({
    queryKey: queryKeys.readiness,
    queryFn: fetchReadiness,
    refetchInterval: 15_000,
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: queryKeys.capabilities,
    queryFn: fetchCapabilities,
    staleTime: 60_000,
  });
}

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: fetchSettings,
    staleTime: 60_000,
  });
}

export function useOppositions() {
  return useQuery({
    queryKey: queryKeys.oppositions,
    queryFn: fetchOppositions,
    staleTime: 30_000,
  });
}

export function useConvocation(convocationId: string | null) {
  return useQuery({
    queryKey: queryKeys.convocation(convocationId ?? 'ninguna'),
    queryFn: () => fetchConvocation(convocationId as string),
    enabled: convocationId !== null,
    staleTime: 60_000,
  });
}

export function useCurriculum(convocationId: string | null) {
  return useQuery({
    queryKey: queryKeys.curriculum(convocationId ?? 'ninguna'),
    queryFn: () => fetchCurriculum(convocationId as string),
    enabled: convocationId !== null,
    staleTime: 60_000,
  });
}

export function useCurriculumNode(nodeId: string | null) {
  return useQuery({
    queryKey: queryKeys.curriculumNode(nodeId ?? 'ninguno'),
    queryFn: () => fetchCurriculumNode(nodeId as string),
    enabled: nodeId !== null,
    staleTime: 60_000,
  });
}

export function useActivateOpposition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: activateOpposition,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.oppositions });
    },
  });
}
