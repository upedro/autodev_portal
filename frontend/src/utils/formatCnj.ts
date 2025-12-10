// Regex para validar formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
export const CNJ_REGEX = /^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$/;

export const formatCNJ = (value: string): string => {
  // Remove tudo que não é número
  const numbers = value.replace(/\D/g, '');
  
  // Aplica a máscara
  if (numbers.length <= 7) {
    return numbers;
  } else if (numbers.length <= 9) {
    return `${numbers.slice(0, 7)}-${numbers.slice(7)}`;
  } else if (numbers.length <= 13) {
    return `${numbers.slice(0, 7)}-${numbers.slice(7, 9)}.${numbers.slice(9)}`;
  } else if (numbers.length <= 14) {
    return `${numbers.slice(0, 7)}-${numbers.slice(7, 9)}.${numbers.slice(9, 13)}.${numbers.slice(13)}`;
  } else if (numbers.length <= 16) {
    return `${numbers.slice(0, 7)}-${numbers.slice(7, 9)}.${numbers.slice(9, 13)}.${numbers.slice(13, 14)}.${numbers.slice(14)}`;
  } else {
    return `${numbers.slice(0, 7)}-${numbers.slice(7, 9)}.${numbers.slice(9, 13)}.${numbers.slice(13, 14)}.${numbers.slice(14, 16)}.${numbers.slice(16, 20)}`;
  }
};

export const validateCNJ = (cnj: string): boolean => {
  return CNJ_REGEX.test(cnj);
};

export const cleanCNJ = (cnj: string): string => {
  return cnj.replace(/\D/g, '');
};

export const parseCNJList = (text: string): string[] => {
  return text
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0);
};
