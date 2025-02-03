import React from 'react';
import { Alert, AlertProps } from '@mui/material';

interface CustomAlertProps extends AlertProps {
  message: string;
}

const CustomAlert: React.FC<CustomAlertProps> = ({ message, ...props }) => {
  return (
    <Alert elevation={6} variant="filled" {...props}>
      {message}
    </Alert>
  );
};

export default CustomAlert;
